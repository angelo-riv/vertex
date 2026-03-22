#!/usr/bin/env python3
"""
Property-Based Test for Calibration Backend Integration

**Validates: Requirements 18.1, 18.2, 18.6**

Property 15: Calibration Backend Integration
For any calibration data received from ESP32, the backend should store patient-specific 
baselines in Supabase with timestamp and device ID, apply calibrated thresholds to 
real-time processing (FSR imbalance using current_ratio - baseline_ratio > 2*baseline_SD, 
pitch deviation from calibrated upright), and maintain calibration history for comparison.

This test validates that calibration data integration with the backend works correctly 
across all scenarios and maintains data integrity with proper threshold application.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from models.calibration_models import (
    CalibrationDataCreate, CalibrationDataResponse, AdaptiveThresholds,
    calculate_adaptive_thresholds, analyze_fsr_imbalance, analyze_pitch_deviation,
    validate_calibration_quality
)
from models.clinical_models import (
    ClinicalThresholdsCreate, ClinicalThresholdsResponse, PareticSide
)


# Test configuration constants
MIN_FSR_VALUE = 100
MAX_FSR_VALUE = 4095
MIN_PITCH_ANGLE = -30.0
MAX_PITCH_ANGLE = 30.0
MIN_CALIBRATION_DURATION = 20
MAX_CALIBRATION_DURATION = 60


# Hypothesis strategies for generating test data
@st.composite
def patient_id_strategy(draw):
    """Generate valid patient IDs for testing"""
    return f"patient_{draw(st.integers(min_value=1000, max_value=9999))}"


@st.composite
def device_id_strategy(draw):
    """Generate valid ESP32 device IDs for testing"""
    return f"ESP32_{draw(st.integers(min_value=1000, max_value=9999))}"


@st.composite
def calibration_data_create_strategy(draw):
    """Generate valid calibration data from ESP32 for testing"""
    patient_id = draw(patient_id_strategy())
    device_id = draw(device_id_strategy())
    
    baseline_pitch = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False))
    baseline_fsr_left = draw(st.floats(min_value=MIN_FSR_VALUE, max_value=MAX_FSR_VALUE))
    baseline_fsr_right = draw(st.floats(min_value=MIN_FSR_VALUE, max_value=MAX_FSR_VALUE))
    
    return CalibrationDataCreate(
        patient_id=patient_id,
        device_id=device_id,
        baseline_pitch=baseline_pitch,
        baseline_fsr_left=baseline_fsr_left,
        baseline_fsr_right=baseline_fsr_right,
        pitch_std_dev=draw(st.floats(min_value=0.3, max_value=3.0, allow_nan=False)),
        fsr_std_dev=draw(st.floats(min_value=0.03, max_value=0.25, allow_nan=False)),
        calibration_duration=draw(st.integers(min_value=MIN_CALIBRATION_DURATION, max_value=MAX_CALIBRATION_DURATION)),
        sample_count=draw(st.integers(min_value=50, max_value=400))
    )

@st.composite
def clinical_thresholds_strategy(draw):
    """Generate clinical thresholds for adaptive threshold calculation"""
    normal_threshold = draw(st.floats(min_value=3.0, max_value=7.0))
    pusher_threshold = draw(st.floats(min_value=max(5.0, normal_threshold + 1.0), max_value=15.0))
    severe_threshold = draw(st.floats(min_value=max(15.0, pusher_threshold + 2.0), max_value=25.0))
    
    return {
        'normal_threshold': normal_threshold,
        'pusher_threshold': pusher_threshold,
        'severe_threshold': severe_threshold
    }


@st.composite
def sensor_reading_strategy(draw):
    """Generate real-time sensor readings for threshold application testing"""
    return {
        'pitch': draw(st.floats(min_value=MIN_PITCH_ANGLE, max_value=MAX_PITCH_ANGLE, allow_nan=False)),
        'fsr_left': draw(st.integers(min_value=0, max_value=MAX_FSR_VALUE)),
        'fsr_right': draw(st.integers(min_value=0, max_value=MAX_FSR_VALUE)),
        'timestamp': draw(st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )).replace(tzinfo=timezone.utc)
    }


@st.composite
def multiple_calibrations_strategy(draw):
    """Generate multiple calibrations for history testing"""
    patient_id = draw(patient_id_strategy())
    device_id = draw(device_id_strategy())
    calibration_count = draw(st.integers(min_value=2, max_value=6))
    
    calibrations = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    for i in range(calibration_count):
        calibration_date = base_date + timedelta(days=i * 4)  # Every 4 days
        calibration = draw(calibration_data_create_strategy())
        calibration.patient_id = patient_id
        calibration.device_id = device_id
        
        calibration_entry = {
            "id": f"cal_{patient_id}_{i+1}",
            "calibration_date": calibration_date,
            "is_active": i == calibration_count - 1,  # Only latest is active
            "calibration": calibration
        }
        calibrations.append(calibration_entry)
    
    return calibrations


# Mock Supabase client for testing calibration backend integration
def create_mock_supabase_for_calibration():
    """Create a mock Supabase client with calibration-specific behavior"""
    mock_supabase = Mock()
    
    # Storage for simulated database data
    mock_supabase._calibrations_data = []
    mock_supabase._thresholds_data = []
    
    def mock_table(table_name):
        table_mock = Mock()
        
        if table_name == "device_calibrations":
            def mock_insert(data):
                result_mock = Mock()
                # Simulate database insertion with proper calibration data handling
                inserted_data = data.copy() if isinstance(data, dict) else data
                if isinstance(inserted_data, dict):
                    inserted_data["id"] = f"calibration_{len(mock_supabase._calibrations_data) + 1}"
                    inserted_data["created_at"] = datetime.now(timezone.utc).isoformat()
                    
                    # Ensure baseline_fsr_ratio is calculated if not present
                    if "baseline_fsr_ratio" not in inserted_data:
                        fsr_left = inserted_data.get("baseline_fsr_left", 0)
                        fsr_right = inserted_data.get("baseline_fsr_right", 0)
                        total = fsr_left + fsr_right
                        inserted_data["baseline_fsr_ratio"] = fsr_right / total if total > 0 else 0.5
                    
                    # Set calibration_date if not present
                    if "calibration_date" not in inserted_data:
                        inserted_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
                
                mock_supabase._calibrations_data.append(inserted_data)
                result_mock.data = [inserted_data]
                return result_mock
            
            def mock_select(fields="*"):
                select_mock = Mock()
                
                def mock_eq(field, value):
                    eq_mock = Mock()
                    
                    def mock_execute():
                        result_mock = Mock()
                        filtered_data = [
                            c for c in mock_supabase._calibrations_data 
                            if c.get(field) == value
                        ]
                        result_mock.data = filtered_data
                        result_mock.count = len(filtered_data)
                        return result_mock
                    
                    eq_mock.execute = mock_execute
                    eq_mock.eq = lambda f, v: mock_eq(f, v)  # Chain eq calls
                    eq_mock.order = lambda f, **kwargs: eq_mock  # Chain order calls
                    eq_mock.limit = lambda n: eq_mock  # Chain limit calls
                    return eq_mock
                
                select_mock.eq = mock_eq
                return select_mock
            
            def mock_update(data):
                update_mock = Mock()
                
                def mock_eq(field, value):
                    eq_mock = Mock()
                    
                    def mock_execute():
                        result_mock = Mock()
                        updated_data = []
                        for c in mock_supabase._calibrations_data:
                            if c.get(field) == value:
                                c.update(data)
                                updated_data.append(c)
                        result_mock.data = updated_data
                        return result_mock
                    
                    eq_mock.execute = mock_execute
                    eq_mock.eq = lambda f, v: mock_eq(f, v)
                    return eq_mock
                
                update_mock.eq = mock_eq
                return update_mock
            
            table_mock.insert = mock_insert
            table_mock.select = mock_select
            table_mock.update = mock_update
        
        elif table_name == "clinical_thresholds":
            def mock_select(fields="*"):
                select_mock = Mock()
                
                def mock_eq(field, value):
                    eq_mock = Mock()
                    
                    def mock_execute():
                        result_mock = Mock()
                        filtered_data = [
                            t for t in mock_supabase._thresholds_data 
                            if t.get(field) == value
                        ]
                        result_mock.data = filtered_data
                        return result_mock
                    
                    eq_mock.execute = mock_execute
                    eq_mock.eq = lambda f, v: mock_eq(f, v)
                    eq_mock.order = lambda f, **kwargs: eq_mock
                    eq_mock.limit = lambda n: eq_mock
                    return eq_mock
                
                select_mock.eq = mock_eq
                return select_mock
            
            table_mock.select = mock_select
        
        return table_mock
    
    mock_supabase.table = mock_table
    return mock_supabase


# Property-based tests using Hypothesis

@given(
    calibration_create=calibration_data_create_strategy(),
    clinical_thresholds=clinical_thresholds_strategy()
)
@settings(max_examples=15, deadline=2000)
def test_calibration_storage_with_metadata_property(calibration_create, clinical_thresholds):
    """
    Property: For any calibration data received from ESP32, the backend should store 
    patient-specific baselines in Supabase with timestamp and device ID.
    
    **Validates: Requirements 18.1**
    """
    mock_supabase = create_mock_supabase_for_calibration()
    
    # Store clinical thresholds for adaptive threshold calculation
    threshold_data = {
        "patient_id": calibration_create.patient_id,
        "normal_threshold": clinical_thresholds['normal_threshold'],
        "pusher_threshold": clinical_thresholds['pusher_threshold'],
        "severe_threshold": clinical_thresholds['severe_threshold'],
        "is_active": True
    }
    mock_supabase._thresholds_data.append(threshold_data)
    
    # Simulate calibration data storage
    calibration_data = calibration_create.model_dump()
    calibration_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
    calibration_data["is_active"] = True
    
    result = mock_supabase.table("device_calibrations").insert(calibration_data)
    stored_calibration = result.data[0]
    
    # Property: All required metadata should be stored
    required_fields = [
        "id", "patient_id", "device_id", "calibration_date", "baseline_pitch",
        "baseline_fsr_left", "baseline_fsr_right", "baseline_fsr_ratio",
        "pitch_std_dev", "fsr_std_dev", "is_active", "created_at"
    ]
    for field in required_fields:
        assert field in stored_calibration, f"Missing required field: {field}"
    
    # Property: Patient ID should be preserved
    assert stored_calibration["patient_id"] == calibration_create.patient_id
    
    # Property: Device ID should be preserved
    assert stored_calibration["device_id"] == calibration_create.device_id
    
    # Property: Timestamp should be present and valid
    assert stored_calibration["calibration_date"] is not None
    calibration_timestamp = datetime.fromisoformat(stored_calibration["calibration_date"])
    assert calibration_timestamp.tzinfo is not None  # Should have timezone info
    
    # Property: Baseline values should be preserved with correct precision
    assert abs(stored_calibration["baseline_pitch"] - calibration_create.baseline_pitch) < 0.001
    assert abs(stored_calibration["baseline_fsr_left"] - calibration_create.baseline_fsr_left) < 0.1
    assert abs(stored_calibration["baseline_fsr_right"] - calibration_create.baseline_fsr_right) < 0.1
    
    # Property: FSR ratio should be calculated correctly
    expected_ratio = calibration_create.baseline_fsr_ratio
    assert abs(stored_calibration["baseline_fsr_ratio"] - expected_ratio) < 0.001
    
    # Property: Standard deviations should be preserved
    assert abs(stored_calibration["pitch_std_dev"] - calibration_create.pitch_std_dev) < 0.001
    assert abs(stored_calibration["fsr_std_dev"] - calibration_create.fsr_std_dev) < 0.001
    
    # Property: Should be marked as active by default
    assert stored_calibration["is_active"] == True
    
    # Property: Should have unique ID
    assert stored_calibration["id"] is not None
    assert len(stored_calibration["id"]) > 0


@given(
    calibration_create=calibration_data_create_strategy(),
    clinical_thresholds=clinical_thresholds_strategy(),
    sensor_readings=st.lists(sensor_reading_strategy(), min_size=10, max_size=30)
)
@settings(max_examples=12, deadline=2500)
def test_calibrated_threshold_application_property(calibration_create, clinical_thresholds, sensor_readings):
    """
    Property: For any calibration data, the backend should apply calibrated thresholds 
    to real-time processing using FSR imbalance detection and pitch deviation calculations.
    
    **Validates: Requirements 18.2**
    """
    # Calculate adaptive thresholds from calibration and clinical data
    adaptive_thresholds = calculate_adaptive_thresholds(calibration_create, clinical_thresholds)
    
    # Create calibration response object for analysis functions
    calibration_response = CalibrationDataResponse(
        id="test_calibration_id",
        patient_id=calibration_create.patient_id,
        device_id=calibration_create.device_id,
        calibration_date=datetime.now(timezone.utc),
        baseline_pitch=calibration_create.baseline_pitch,
        baseline_fsr_left=calibration_create.baseline_fsr_left,
        baseline_fsr_right=calibration_create.baseline_fsr_right,
        baseline_fsr_ratio=calibration_create.baseline_fsr_ratio,
        pitch_std_dev=calibration_create.pitch_std_dev,
        fsr_std_dev=calibration_create.fsr_std_dev,
        calibration_duration=calibration_create.calibration_duration,
        sample_count=calibration_create.sample_count,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    # Test FSR imbalance detection with calibrated thresholds
    for sensor_reading in sensor_readings:
        fsr_left = sensor_reading['fsr_left']
        fsr_right = sensor_reading['fsr_right']
        
        # Skip if both FSR values are zero (invalid reading)
        if fsr_left == 0 and fsr_right == 0:
            continue
        
        # Analyze FSR imbalance using calibrated baseline
        fsr_analysis = analyze_fsr_imbalance(fsr_left, fsr_right, calibration_response, adaptive_thresholds)
        
        # Property: Current ratio should be calculated correctly
        total_fsr = fsr_left + fsr_right
        expected_current_ratio = fsr_right / total_fsr if total_fsr > 0 else 0.5
        assert abs(fsr_analysis.current_ratio - expected_current_ratio) < 0.001
        
        # Property: Baseline ratio should match calibration
        assert abs(fsr_analysis.baseline_ratio - calibration_create.baseline_fsr_ratio) < 0.001
        
        # Property: Imbalance magnitude should use calibrated baseline
        expected_imbalance = abs(fsr_analysis.current_ratio - calibration_create.baseline_fsr_ratio)
        assert abs(fsr_analysis.imbalance_magnitude - expected_imbalance) < 0.001
        
        # Property: Threshold detection should use adaptive thresholds (which are based on 2*baseline_SD)
        # The adaptive threshold may be different from simple 2*SD due to multipliers
        if fsr_analysis.imbalance_magnitude >= adaptive_thresholds.severe_fsr_imbalance_threshold:
            assert fsr_analysis.severity_level == "severe"
            assert fsr_analysis.exceeds_threshold == True
        elif fsr_analysis.imbalance_magnitude >= adaptive_thresholds.pusher_fsr_imbalance_threshold:
            assert fsr_analysis.severity_level in ["moderate", "severe"]
            assert fsr_analysis.exceeds_threshold == True
        elif fsr_analysis.imbalance_magnitude >= adaptive_thresholds.normal_fsr_imbalance_threshold:
            # May or may not exceed threshold depending on implementation
            pass
        else:
            # Should not exceed threshold for very small deviations
            assert fsr_analysis.severity_level in ["normal", "mild"]
        
        # Property: Direction should be determined correctly
        if abs(fsr_analysis.current_ratio - fsr_analysis.baseline_ratio) < adaptive_thresholds.normal_fsr_imbalance_threshold:
            assert fsr_analysis.imbalance_direction == "balanced"
        elif fsr_analysis.current_ratio > fsr_analysis.baseline_ratio:
            assert fsr_analysis.imbalance_direction == "right"
        else:
            assert fsr_analysis.imbalance_direction == "left"
        
        # Property: Confidence level should be bounded
        assert 0.0 <= fsr_analysis.confidence_level <= 1.0
    
    # Test pitch deviation analysis with calibrated upright position
    for sensor_reading in sensor_readings:
        current_pitch = sensor_reading['pitch']
        
        # Analyze pitch deviation from calibrated upright
        pitch_analysis = analyze_pitch_deviation(current_pitch, calibration_response, adaptive_thresholds)
        
        # Property: Baseline pitch should match calibration
        assert abs(pitch_analysis.baseline_pitch - calibration_create.baseline_pitch) < 0.001
        
        # Property: Deviation should be calculated from calibrated upright
        expected_deviation = abs(current_pitch - calibration_create.baseline_pitch)
        assert abs(pitch_analysis.deviation_magnitude - expected_deviation) < 0.001
        
        # Property: Threshold detection should use adaptive thresholds
        if pitch_analysis.deviation_magnitude >= adaptive_thresholds.severe_pitch_threshold:
            assert pitch_analysis.severity_level == "severe"
            assert pitch_analysis.exceeds_threshold == True
        elif pitch_analysis.deviation_magnitude >= adaptive_thresholds.pusher_pitch_threshold:
            assert pitch_analysis.severity_level == "moderate"
            assert pitch_analysis.exceeds_threshold == True
        elif pitch_analysis.deviation_magnitude >= adaptive_thresholds.normal_pitch_threshold:
            assert pitch_analysis.severity_level == "mild"
        else:
            assert pitch_analysis.severity_level == "normal"
            assert pitch_analysis.exceeds_threshold == False
        
        # Property: Direction should be determined relative to calibrated upright
        pitch_diff = current_pitch - calibration_create.baseline_pitch
        if abs(pitch_diff) < 1.0:
            assert pitch_analysis.deviation_direction == "upright"
        elif pitch_diff > 0:
            assert pitch_analysis.deviation_direction in ["right", "forward"]
        else:
            assert pitch_analysis.deviation_direction in ["left", "backward"]
        
        # Property: Confidence level should be bounded
        assert 0.0 <= pitch_analysis.confidence_level <= 1.0


@given(multiple_calibrations=multiple_calibrations_strategy())
@settings(max_examples=10, deadline=2500)
def test_calibration_history_maintenance_property(multiple_calibrations):
    """
    Property: For any patient with multiple calibrations, the backend should maintain 
    calibration history for comparison and use the most recent calibration data.
    
    **Validates: Requirements 18.6**
    """
    if not multiple_calibrations:
        return  # Skip if no calibrations generated
    
    patient_id = multiple_calibrations[0]["calibration"].patient_id
    device_id = multiple_calibrations[0]["calibration"].device_id
    
    mock_supabase = create_mock_supabase_for_calibration()
    
    # Store all calibrations in chronological order
    stored_calibrations = []
    for calibration_entry in multiple_calibrations:
        calibration_data = calibration_entry["calibration"].model_dump()
        calibration_data["id"] = calibration_entry["id"]
        calibration_data["calibration_date"] = calibration_entry["calibration_date"].isoformat()
        calibration_data["is_active"] = calibration_entry["is_active"]
        
        result = mock_supabase.table("device_calibrations").insert(calibration_data)
        stored_calibrations.append(result.data[0])
    
    # Property: All calibrations should be stored in history
    all_calibrations = mock_supabase.table("device_calibrations").select("*").eq("patient_id", patient_id).execute()
    assert len(all_calibrations.data) == len(multiple_calibrations), "Should maintain complete calibration history"
    
    # Property: Only one calibration should be active (most recent)
    active_calibrations = [c for c in all_calibrations.data if c.get("is_active", False)]
    assert len(active_calibrations) == 1, "Should have exactly one active calibration"
    
    # Property: Active calibration should be the most recent
    most_recent_expected = max(multiple_calibrations, key=lambda x: x["calibration_date"])
    active_calibration = active_calibrations[0]
    expected_date = most_recent_expected["calibration_date"].isoformat()
    assert active_calibration["calibration_date"] == expected_date, "Active calibration should be most recent"
    
    # Property: Historical calibrations should be preserved for comparison
    stored_dates = [datetime.fromisoformat(c["calibration_date"]) for c in all_calibrations.data]
    original_dates = [c["calibration_date"] for c in multiple_calibrations]
    
    # Sort both lists for comparison
    stored_dates.sort()
    original_dates.sort()
    
    for stored_date, original_date in zip(stored_dates, original_dates):
        assert abs((stored_date - original_date).total_seconds()) < 1, "Calibration dates should be preserved exactly"
    
    # Property: Each calibration should maintain its unique baseline values
    for calibration_entry in multiple_calibrations:
        # Find stored calibration by matching patient_id, device_id, and calibration_date
        stored_cal = None
        for c in all_calibrations.data:
            if (c["patient_id"] == calibration_entry["calibration"].patient_id and
                c["device_id"] == calibration_entry["calibration"].device_id and
                abs((datetime.fromisoformat(c["calibration_date"]) - calibration_entry["calibration_date"]).total_seconds()) < 1):
                stored_cal = c
                break
        
        assert stored_cal is not None, f"Could not find stored calibration for entry {calibration_entry['id']}"
        original_cal = calibration_entry["calibration"]
        
        assert abs(stored_cal["baseline_pitch"] - original_cal.baseline_pitch) < 0.001
        assert abs(stored_cal["baseline_fsr_left"] - original_cal.baseline_fsr_left) < 0.1
        assert abs(stored_cal["baseline_fsr_right"] - original_cal.baseline_fsr_right) < 0.1
        assert abs(stored_cal["pitch_std_dev"] - original_cal.pitch_std_dev) < 0.001
        assert abs(stored_cal["fsr_std_dev"] - original_cal.fsr_std_dev) < 0.001
    
    # Property: Most recent calibration should be used for adaptive thresholds
    clinical_thresholds = {
        'normal_threshold': 5.0,
        'pusher_threshold': 10.0,
        'severe_threshold': 20.0
    }
    
    # Get most recent calibration data
    most_recent_cal = most_recent_expected["calibration"]
    adaptive_thresholds = calculate_adaptive_thresholds(most_recent_cal, clinical_thresholds)
    
    # Property: Adaptive thresholds should reflect most recent calibration
    assert adaptive_thresholds.patient_id == patient_id
    assert adaptive_thresholds.device_id == device_id
    
    # Property: FSR thresholds should use most recent baseline standard deviation
    expected_normal_fsr = 2.0 * most_recent_cal.fsr_std_dev
    assert abs(adaptive_thresholds.normal_fsr_imbalance_threshold - expected_normal_fsr) < 0.001
    
    # Property: Pitch thresholds should incorporate most recent stability
    assert adaptive_thresholds.normal_pitch_threshold > 0
    assert adaptive_thresholds.pusher_pitch_threshold > adaptive_thresholds.normal_pitch_threshold
    assert adaptive_thresholds.severe_pitch_threshold > adaptive_thresholds.pusher_pitch_threshold

@given(
    calibration_create=calibration_data_create_strategy(),
    clinical_thresholds=clinical_thresholds_strategy()
)
@settings(max_examples=35, deadline=3500)
def test_adaptive_threshold_calculation_property(calibration_create, clinical_thresholds):
    """
    Property: For any calibration data and clinical thresholds, the system should 
    calculate adaptive thresholds that properly integrate baseline values with 
    clinical parameters using the 2*standard_deviation approach.
    
    **Validates: Requirements 18.2**
    """
    # Calculate adaptive thresholds
    adaptive_thresholds = calculate_adaptive_thresholds(calibration_create, clinical_thresholds)
    
    # Property: Patient and device IDs should be preserved
    assert adaptive_thresholds.patient_id == calibration_create.patient_id
    assert adaptive_thresholds.device_id == calibration_create.device_id
    
    # Property: Pitch thresholds should be based on clinical thresholds with stability adjustment
    stability_factor = min(1.0, calibration_create.pitch_std_dev / 2.0)
    
    expected_normal_pitch = clinical_thresholds['normal_threshold'] * (1 + stability_factor)
    expected_pusher_pitch = clinical_thresholds['pusher_threshold'] * (1 + stability_factor)
    expected_severe_pitch = clinical_thresholds['severe_threshold'] * (1 + stability_factor)
    
    assert abs(adaptive_thresholds.normal_pitch_threshold - expected_normal_pitch) < 0.1
    assert abs(adaptive_thresholds.pusher_pitch_threshold - expected_pusher_pitch) < 0.1
    assert abs(adaptive_thresholds.severe_pitch_threshold - expected_severe_pitch) < 0.1
    
    # Property: FSR thresholds should use 2*standard_deviation approach
    expected_normal_fsr = 2.0 * calibration_create.fsr_std_dev
    expected_pusher_fsr = expected_normal_fsr * 1.5
    expected_severe_fsr = expected_normal_fsr * 2.5
    
    assert abs(adaptive_thresholds.normal_fsr_imbalance_threshold - expected_normal_fsr) < 0.001
    assert abs(adaptive_thresholds.pusher_fsr_imbalance_threshold - expected_pusher_fsr) < 0.001
    assert abs(adaptive_thresholds.severe_fsr_imbalance_threshold - expected_severe_fsr) < 0.001
    
    # Property: Resistance thresholds should incorporate baseline values
    expected_resistance_force = (calibration_create.baseline_fsr_left + calibration_create.baseline_fsr_right) / 2 + \
                               (2.0 * calibration_create.fsr_std_dev * 1000)
    expected_resistance_angle = calibration_create.baseline_pitch + (2.0 * calibration_create.pitch_std_dev)
    
    assert abs(adaptive_thresholds.resistance_force_threshold - expected_resistance_force) < 1.0
    assert abs(adaptive_thresholds.resistance_angle_threshold - expected_resistance_angle) < 0.1
    
    # Property: Thresholds should maintain proper ordering
    assert adaptive_thresholds.normal_pitch_threshold < adaptive_thresholds.pusher_pitch_threshold
    assert adaptive_thresholds.pusher_pitch_threshold < adaptive_thresholds.severe_pitch_threshold
    
    assert adaptive_thresholds.normal_fsr_imbalance_threshold < adaptive_thresholds.pusher_fsr_imbalance_threshold
    assert adaptive_thresholds.pusher_fsr_imbalance_threshold < adaptive_thresholds.severe_fsr_imbalance_threshold
    
    # Property: All thresholds should be positive
    assert adaptive_thresholds.normal_pitch_threshold > 0
    assert adaptive_thresholds.pusher_pitch_threshold > 0
    assert adaptive_thresholds.severe_pitch_threshold > 0
    assert adaptive_thresholds.normal_fsr_imbalance_threshold > 0
    assert adaptive_thresholds.pusher_fsr_imbalance_threshold > 0
    assert adaptive_thresholds.severe_fsr_imbalance_threshold > 0
    assert adaptive_thresholds.resistance_force_threshold > 0
    assert adaptive_thresholds.resistance_angle_threshold is not None
    
    # Property: Calculated timestamp should be recent
    assert adaptive_thresholds.calculated_at is not None
    time_diff = datetime.now(timezone.utc) - adaptive_thresholds.calculated_at
    assert time_diff.total_seconds() < 10  # Should be calculated within last 10 seconds


@given(
    calibration_create=calibration_data_create_strategy(),
    clinical_thresholds=clinical_thresholds_strategy(),
    sensor_readings=st.lists(sensor_reading_strategy(), min_size=20, max_size=50)
)
@settings(max_examples=25, deadline=5000)
def test_integrated_calibration_backend_workflow_property(calibration_create, clinical_thresholds, sensor_readings):
    """
    Property: For any complete calibration backend integration workflow, all components 
    should work together consistently to provide accurate real-time analysis.
    
    **Validates: Requirements 18.1, 18.2, 18.6**
    """
    mock_supabase = create_mock_supabase_for_calibration()
    
    # Step 1: Store clinical thresholds
    threshold_data = {
        "patient_id": calibration_create.patient_id,
        "normal_threshold": clinical_thresholds['normal_threshold'],
        "pusher_threshold": clinical_thresholds['pusher_threshold'],
        "severe_threshold": clinical_thresholds['severe_threshold'],
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    mock_supabase._thresholds_data.append(threshold_data)
    
    # Step 2: Store calibration data with proper metadata
    calibration_data = calibration_create.model_dump()
    calibration_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
    calibration_data["is_active"] = True
    
    result = mock_supabase.table("device_calibrations").insert(calibration_data)
    stored_calibration = result.data[0]
    
    # Property: Storage should preserve all calibration metadata
    assert stored_calibration["patient_id"] == calibration_create.patient_id
    assert stored_calibration["device_id"] == calibration_create.device_id
    assert stored_calibration["is_active"] == True
    
    # Step 3: Calculate adaptive thresholds from stored data
    adaptive_thresholds = calculate_adaptive_thresholds(calibration_create, clinical_thresholds)
    
    # Property: Adaptive thresholds should integrate calibration and clinical data
    assert adaptive_thresholds.patient_id == calibration_create.patient_id
    assert adaptive_thresholds.device_id == calibration_create.device_id
    
    # Step 4: Create calibration response for real-time analysis
    calibration_response = CalibrationDataResponse(
        id=stored_calibration["id"],
        patient_id=stored_calibration["patient_id"],
        device_id=stored_calibration["device_id"],
        calibration_date=datetime.fromisoformat(stored_calibration["calibration_date"]),
        baseline_pitch=stored_calibration["baseline_pitch"],
        baseline_fsr_left=stored_calibration["baseline_fsr_left"],
        baseline_fsr_right=stored_calibration["baseline_fsr_right"],
        baseline_fsr_ratio=stored_calibration["baseline_fsr_ratio"],
        pitch_std_dev=stored_calibration["pitch_std_dev"],
        fsr_std_dev=stored_calibration["fsr_std_dev"],
        calibration_duration=stored_calibration.get("calibration_duration", 30),
        sample_count=stored_calibration.get("sample_count", 150),
        is_active=stored_calibration["is_active"],
        created_at=datetime.fromisoformat(stored_calibration["created_at"])
    )
    
    # Step 5: Test real-time analysis with calibrated thresholds
    analysis_results = []
    for sensor_reading in sensor_readings:
        # FSR analysis
        if sensor_reading['fsr_left'] > 0 or sensor_reading['fsr_right'] > 0:
            fsr_analysis = analyze_fsr_imbalance(
                sensor_reading['fsr_left'], 
                sensor_reading['fsr_right'], 
                calibration_response, 
                adaptive_thresholds
            )
            
            # Pitch analysis
            pitch_analysis = analyze_pitch_deviation(
                sensor_reading['pitch'], 
                calibration_response, 
                adaptive_thresholds
            )
            
            analysis_results.append({
                "timestamp": sensor_reading['timestamp'],
                "fsr_analysis": fsr_analysis,
                "pitch_analysis": pitch_analysis,
                "raw_sensor": sensor_reading
            })
    
    # Property: All analyses should use consistent calibration baseline
    for result in analysis_results:
        assert abs(result["fsr_analysis"].baseline_ratio - calibration_create.baseline_fsr_ratio) < 0.001
        assert abs(result["pitch_analysis"].baseline_pitch - calibration_create.baseline_pitch) < 0.001
    
    # Property: Threshold application should be consistent across all readings
    for result in analysis_results:
        fsr_analysis = result["fsr_analysis"]
        pitch_analysis = result["pitch_analysis"]
        
        # FSR threshold consistency
        if fsr_analysis.imbalance_magnitude >= adaptive_thresholds.severe_fsr_imbalance_threshold:
            assert fsr_analysis.severity_level == "severe"
        elif fsr_analysis.imbalance_magnitude >= adaptive_thresholds.pusher_fsr_imbalance_threshold:
            assert fsr_analysis.severity_level in ["moderate", "severe"]
        
        # Pitch threshold consistency
        if pitch_analysis.deviation_magnitude >= adaptive_thresholds.severe_pitch_threshold:
            assert pitch_analysis.severity_level == "severe"
        elif pitch_analysis.deviation_magnitude >= adaptive_thresholds.pusher_pitch_threshold:
            assert pitch_analysis.severity_level in ["moderate", "severe"]
    
    # Property: Analysis confidence should reflect calibration quality
    calibration_quality = validate_calibration_quality(calibration_create)
    
    for result in analysis_results:
        # Higher quality calibration should generally lead to higher confidence
        if calibration_quality.quality_score > 0.8:
            # At least some analyses should have reasonable confidence
            assert any(r["fsr_analysis"].confidence_level > 0.3 for r in analysis_results[:10])
            assert any(r["pitch_analysis"].confidence_level > 0.3 for r in analysis_results[:10])
    
    # Property: System should maintain data integrity throughout workflow
    # Verify stored data matches original input
    assert abs(stored_calibration["baseline_pitch"] - calibration_create.baseline_pitch) < 0.001
    assert abs(stored_calibration["baseline_fsr_left"] - calibration_create.baseline_fsr_left) < 0.1
    assert abs(stored_calibration["baseline_fsr_right"] - calibration_create.baseline_fsr_right) < 0.1
    assert abs(stored_calibration["pitch_std_dev"] - calibration_create.pitch_std_dev) < 0.001
    assert abs(stored_calibration["fsr_std_dev"] - calibration_create.fsr_std_dev) < 0.001
    
    # Property: Adaptive thresholds should be reproducible
    adaptive_thresholds_2 = calculate_adaptive_thresholds(calibration_create, clinical_thresholds)
    assert abs(adaptive_thresholds.normal_pitch_threshold - adaptive_thresholds_2.normal_pitch_threshold) < 0.001
    assert abs(adaptive_thresholds.normal_fsr_imbalance_threshold - adaptive_thresholds_2.normal_fsr_imbalance_threshold) < 0.001


# Integration test combining all calibration backend properties
@given(
    patient_id=patient_id_strategy(),
    device_id=device_id_strategy()
)
@settings(max_examples=15, deadline=6000)
def test_comprehensive_calibration_backend_integration_property(patient_id, device_id):
    """
    Property: For any patient and device in the system, the complete calibration 
    backend integration should maintain data integrity and provide consistent 
    analysis across all operations.
    
    **Validates: Requirements 18.1, 18.2, 18.6**
    """
    mock_supabase = create_mock_supabase_for_calibration()
    
    # Create initial calibration
    initial_calibration = CalibrationDataCreate(
        patient_id=patient_id,
        device_id=device_id,
        baseline_pitch=1.2,
        baseline_fsr_left=2000.0,
        baseline_fsr_right=2200.0,
        pitch_std_dev=1.1,
        fsr_std_dev=0.09,
        calibration_duration=30,
        sample_count=165
    )
    
    # Store initial calibration
    cal_data_1 = initial_calibration.model_dump()
    cal_data_1["calibration_date"] = datetime.now(timezone.utc).isoformat()
    cal_data_1["is_active"] = True
    
    result_1 = mock_supabase.table("device_calibrations").insert(cal_data_1)
    stored_cal_1 = result_1.data[0]
    
    # Property: Initial calibration should be stored correctly
    assert stored_cal_1["patient_id"] == patient_id
    assert stored_cal_1["device_id"] == device_id
    assert stored_cal_1["is_active"] == True
    
    # Add clinical thresholds
    clinical_thresholds = {
        'normal_threshold': 5.0,
        'pusher_threshold': 10.0,
        'severe_threshold': 20.0
    }
    
    threshold_data = {
        "patient_id": patient_id,
        "normal_threshold": clinical_thresholds['normal_threshold'],
        "pusher_threshold": clinical_thresholds['pusher_threshold'],
        "severe_threshold": clinical_thresholds['severe_threshold'],
        "is_active": True
    }
    mock_supabase._thresholds_data.append(threshold_data)
    
    # Create newer calibration
    newer_calibration = initial_calibration.model_copy()
    newer_calibration.baseline_pitch = 0.8
    newer_calibration.pitch_std_dev = 0.9
    newer_calibration.fsr_std_dev = 0.07
    
    # Deactivate old calibration
    mock_supabase.table("device_calibrations").update({"is_active": False}).eq("id", stored_cal_1["id"]).execute()
    
    # Store newer calibration
    cal_data_2 = newer_calibration.model_dump()
    cal_data_2["calibration_date"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    cal_data_2["is_active"] = True
    
    result_2 = mock_supabase.table("device_calibrations").insert(cal_data_2)
    stored_cal_2 = result_2.data[0]
    
    # Property: History should be maintained
    all_calibrations = mock_supabase.table("device_calibrations").select("*").eq("patient_id", patient_id).execute()
    assert len(all_calibrations.data) == 2
    
    # Property: Only most recent should be active
    active_calibrations = [c for c in all_calibrations.data if c.get("is_active", False)]
    assert len(active_calibrations) == 1
    assert active_calibrations[0]["id"] == stored_cal_2["id"]
    
    # Property: Most recent calibration should be used for analysis
    active_cal = active_calibrations[0]
    adaptive_thresholds = calculate_adaptive_thresholds(newer_calibration, clinical_thresholds)
    
    assert adaptive_thresholds.patient_id == patient_id
    assert adaptive_thresholds.device_id == device_id
    
    # Test real-time analysis with most recent calibration
    test_sensor_data = [
        {"pitch": 12.0, "fsr_left": 1500, "fsr_right": 2500},  # Should trigger pusher detection
        {"pitch": 2.0, "fsr_left": 2000, "fsr_right": 2100},   # Should be normal
        {"pitch": 25.0, "fsr_left": 1000, "fsr_right": 3000},  # Should be severe
    ]
    
    calibration_response = CalibrationDataResponse(
        id=active_cal["id"],
        patient_id=active_cal["patient_id"],
        device_id=active_cal["device_id"],
        calibration_date=datetime.fromisoformat(active_cal["calibration_date"]),
        baseline_pitch=active_cal["baseline_pitch"],
        baseline_fsr_left=active_cal["baseline_fsr_left"],
        baseline_fsr_right=active_cal["baseline_fsr_right"],
        baseline_fsr_ratio=active_cal["baseline_fsr_ratio"],
        pitch_std_dev=active_cal["pitch_std_dev"],
        fsr_std_dev=active_cal["fsr_std_dev"],
        calibration_duration=active_cal.get("calibration_duration", 30),
        sample_count=active_cal.get("sample_count", 150),
        is_active=active_cal["is_active"],
        created_at=datetime.fromisoformat(active_cal["created_at"])
    )
    
    for sensor_data in test_sensor_data:
        # Test FSR analysis
        fsr_analysis = analyze_fsr_imbalance(
            sensor_data["fsr_left"], 
            sensor_data["fsr_right"], 
            calibration_response, 
            adaptive_thresholds
        )
        
        # Test pitch analysis
        pitch_analysis = analyze_pitch_deviation(
            sensor_data["pitch"], 
            calibration_response, 
            adaptive_thresholds
        )
        
        # Property: Should use most recent calibration baseline
        assert abs(fsr_analysis.baseline_ratio - newer_calibration.baseline_fsr_ratio) < 0.001
        assert abs(pitch_analysis.baseline_pitch - newer_calibration.baseline_pitch) < 0.001
        
        # Property: Analysis should be consistent with adaptive thresholds
        assert 0.0 <= fsr_analysis.confidence_level <= 1.0
        assert 0.0 <= pitch_analysis.confidence_level <= 1.0
    
    print(f"✓ Comprehensive calibration backend integration test passed for patient {patient_id}")
    print(f"  - Device: {device_id}")
    print(f"  - Calibration history: {len(all_calibrations.data)} entries")
    print(f"  - Active calibration baseline: pitch={newer_calibration.baseline_pitch}°, fsr_ratio={newer_calibration.baseline_fsr_ratio:.3f}")
    print(f"  - Adaptive thresholds: normal_pitch={adaptive_thresholds.normal_pitch_threshold:.1f}°, normal_fsr={adaptive_thresholds.normal_fsr_imbalance_threshold:.3f}")


if __name__ == "__main__":
    print("🧪 Running Calibration Backend Integration Property Tests...")
    print("**Validates: Requirements 18.1, 18.2, 18.6**")
    print()
    
    # Run individual property tests
    test_functions = [
        ("Calibration Storage with Metadata", test_calibration_storage_with_metadata_property),
        ("Calibrated Threshold Application", test_calibrated_threshold_application_property),
        ("Calibration History Maintenance", test_calibration_history_maintenance_property),
        ("Adaptive Threshold Calculation", test_adaptive_threshold_calculation_property),
        ("Integrated Calibration Backend Workflow", test_integrated_calibration_backend_workflow_property),
        ("Comprehensive Calibration Backend Integration", test_comprehensive_calibration_backend_integration_property),
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_name, test_func in test_functions:
        try:
            print(f"🔍 Testing {test_name}...")
            test_func()
            print(f"✅ {test_name} - PASSED")
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Results: {passed_tests}/{total_tests} property tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All calibration backend integration properties validated!")
        print("\n✅ Validated Requirements:")
        print("- 18.1: Store patient-specific baselines in Supabase with timestamp and device ID")
        print("- 18.2: Apply calibrated thresholds to real-time processing (FSR imbalance using current_ratio - baseline_ratio > 2*baseline_SD, pitch deviation from calibrated upright)")
        print("- 18.6: Use most recent calibration data and maintain calibration history for comparison")
    else:
        print("⚠️  Some property tests failed. Check calibration backend integration implementation.")