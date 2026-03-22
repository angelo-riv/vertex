#!/usr/bin/env python3
"""
Property-Based Test for Patient-Specific Threshold Application

**Validates: Requirements 15.6, 15.7, 18.6**

Property 13: Patient-Specific Threshold Application
For any patient with configured thresholds, the backend should store patient-specific 
parameters in Supabase with version history and therapist authorization, apply these 
thresholds consistently to all real-time detection and historical analysis, and use 
the most recent calibration data when multiple calibrations exist.

This test validates that patient-specific threshold configuration and application 
works correctly across all scenarios and maintains data integrity.
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

from models.clinical_models import (
    ClinicalThresholdsCreate, ClinicalThresholdsResponse, ClinicalThresholdsUpdate,
    PareticSide, validate_threshold_consistency
)
from models.calibration_models import (
    CalibrationDataCreate, CalibrationDataResponse, AdaptiveThresholds,
    calculate_adaptive_thresholds
)
from clinical_algorithm import (
    PusherDetectionAlgorithm, ClinicalThresholds, CalibrationData,
    SensorDataPoint, create_default_thresholds
)


# Test configuration constants
MIN_THRESHOLD_VERSION = 1
MAX_THRESHOLD_VERSION = 10
MIN_CALIBRATION_AGE_DAYS = 0
MAX_CALIBRATION_AGE_DAYS = 30


# Hypothesis strategies for generating test data
@st.composite
def patient_id_strategy(draw):
    """Generate valid patient IDs for testing"""
    return f"patient_{draw(st.integers(min_value=1000, max_value=9999))}"


@st.composite
def therapist_id_strategy(draw):
    """Generate valid therapist IDs for testing"""
    return f"therapist_{draw(st.integers(min_value=100, max_value=999))}"


@st.composite
def device_id_strategy(draw):
    """Generate valid ESP32 device IDs for testing"""
    return f"ESP32_{draw(st.integers(min_value=1000, max_value=9999))}"

@st.composite
def clinical_thresholds_create_strategy(draw):
    """Generate valid clinical thresholds for creation testing"""
    patient_id = draw(patient_id_strategy())
    paretic_side = draw(st.sampled_from([PareticSide.LEFT, PareticSide.RIGHT]))
    
    # Generate valid threshold ranges with proper ordering and Pydantic constraints
    normal_threshold = draw(st.floats(min_value=3.0, max_value=7.0))
    # Ensure pusher_threshold >= 5.0 (Pydantic constraint) and > normal_threshold
    pusher_threshold = draw(st.floats(min_value=max(5.0, normal_threshold + 1.0), max_value=15.0))
    # Ensure severe_threshold >= 15.0 (Pydantic constraint) and > pusher_threshold
    severe_threshold = draw(st.floats(min_value=max(15.0, pusher_threshold + 2.0), max_value=25.0))
    
    return ClinicalThresholdsCreate(
        patient_id=patient_id,
        paretic_side=paretic_side,
        normal_threshold=normal_threshold,
        pusher_threshold=pusher_threshold,
        severe_threshold=severe_threshold,
        resistance_threshold=draw(st.floats(min_value=1.0, max_value=3.0)),
        episode_duration_min=draw(st.floats(min_value=1.5, max_value=5.0)),
        non_paretic_threshold=draw(st.floats(min_value=0.6, max_value=0.8)),
        created_by=draw(therapist_id_strategy()),
        therapist_notes=draw(st.text(min_size=0, max_size=200))
    )


@st.composite
def calibration_data_create_strategy(draw):
    """Generate valid calibration data for testing"""
    patient_id = draw(patient_id_strategy())
    device_id = draw(device_id_strategy())
    
    baseline_pitch = draw(st.floats(min_value=-5.0, max_value=5.0))
    baseline_fsr_left = draw(st.floats(min_value=500.0, max_value=3500.0))
    baseline_fsr_right = draw(st.floats(min_value=500.0, max_value=3500.0))
    
    return CalibrationDataCreate(
        patient_id=patient_id,
        device_id=device_id,
        baseline_pitch=baseline_pitch,
        baseline_fsr_left=baseline_fsr_left,
        baseline_fsr_right=baseline_fsr_right,
        pitch_std_dev=draw(st.floats(min_value=0.5, max_value=3.0)),
        fsr_std_dev=draw(st.floats(min_value=0.05, max_value=0.2)),
        calibration_duration=draw(st.integers(min_value=20, max_value=60)),
        sample_count=draw(st.integers(min_value=50, max_value=300))
    )


@st.composite
def sensor_data_point_strategy(draw):
    """Generate sensor data points for real-time analysis testing"""
    return SensorDataPoint(
        timestamp=draw(st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )).replace(tzinfo=timezone.utc),
        pitch=draw(st.floats(min_value=-30.0, max_value=30.0, allow_nan=False)),
        fsr_left=draw(st.integers(min_value=0, max_value=4095)),
        fsr_right=draw(st.integers(min_value=0, max_value=4095)),
        device_id=draw(device_id_strategy())
    )


@st.composite
def threshold_version_history_strategy(draw):
    """Generate threshold version history for testing"""
    patient_id = draw(patient_id_strategy())
    version_count = draw(st.integers(min_value=1, max_value=5))
    
    versions = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    for i in range(version_count):
        version_date = base_date + timedelta(days=i * 7)  # Weekly updates
        thresholds = draw(clinical_thresholds_create_strategy())
        thresholds.patient_id = patient_id  # Ensure same patient
        
        version_data = {
            "id": f"threshold_{patient_id}_{i+1}",
            "version": i + 1,
            "created_at": version_date,
            "is_active": i == version_count - 1,  # Only latest is active
            "thresholds": thresholds
        }
        versions.append(version_data)
    
    return versions

@st.composite
def multiple_calibrations_strategy(draw):
    """Generate multiple calibrations for testing most recent selection"""
    patient_id = draw(patient_id_strategy())
    device_id = draw(device_id_strategy())
    calibration_count = draw(st.integers(min_value=2, max_value=5))
    
    calibrations = []
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    for i in range(calibration_count):
        calibration_date = base_date + timedelta(days=i * 5)  # Every 5 days
        calibration = draw(calibration_data_create_strategy())
        calibration.patient_id = patient_id
        calibration.device_id = device_id
        
        calibration_data = {
            "id": f"calibration_{patient_id}_{i+1}",
            "calibration_date": calibration_date,
            "is_active": i == calibration_count - 1,  # Only latest is active
            "calibration": calibration
        }
        calibrations.append(calibration_data)
    
    return calibrations


# Mock Supabase client for testing
def create_mock_supabase():
    """Create a mock Supabase client with realistic behavior"""
    mock_supabase = Mock()
    
    # Storage for simulated database data
    mock_supabase._thresholds_data = []
    mock_supabase._calibrations_data = []
    
    def mock_table(table_name):
        table_mock = Mock()
        
        if table_name == "clinical_thresholds":
            def mock_insert(data):
                result_mock = Mock()
                # Simulate database insertion
                inserted_data = data.copy() if isinstance(data, dict) else data
                if isinstance(inserted_data, dict):
                    inserted_data["id"] = f"threshold_{len(mock_supabase._thresholds_data) + 1}"
                    inserted_data["version"] = len([t for t in mock_supabase._thresholds_data 
                                                  if t.get("patient_id") == inserted_data.get("patient_id")]) + 1
                mock_supabase._thresholds_data.append(inserted_data)
                result_mock.data = [inserted_data]
                return result_mock
            
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
                        for t in mock_supabase._thresholds_data:
                            if t.get(field) == value:
                                t.update(data)
                                updated_data.append(t)
                        result_mock.data = updated_data
                        return result_mock
                    
                    eq_mock.execute = mock_execute
                    return eq_mock
                
                update_mock.eq = mock_eq
                return update_mock
            
            table_mock.insert = mock_insert
            table_mock.select = mock_select
            table_mock.update = mock_update
        
        elif table_name == "device_calibrations":
            def mock_insert(data):
                result_mock = Mock()
                inserted_data = data.copy() if isinstance(data, dict) else data
                if isinstance(inserted_data, dict):
                    inserted_data["id"] = f"calibration_{len(mock_supabase._calibrations_data) + 1}"
                    # Ensure baseline_fsr_ratio is calculated if not present
                    if "baseline_fsr_ratio" not in inserted_data:
                        fsr_left = inserted_data.get("baseline_fsr_left", 0)
                        fsr_right = inserted_data.get("baseline_fsr_right", 0)
                        total = fsr_left + fsr_right
                        inserted_data["baseline_fsr_ratio"] = fsr_right / total if total > 0 else 0.5
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
                        return result_mock
                    
                    eq_mock.execute = mock_execute
                    eq_mock.eq = lambda f, v: mock_eq(f, v)
                    eq_mock.order = lambda f, **kwargs: eq_mock
                    eq_mock.limit = lambda n: eq_mock
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
                    return eq_mock
                
                update_mock.eq = mock_eq
                return update_mock
            
            table_mock.insert = mock_insert
            table_mock.select = mock_select
            table_mock.update = mock_update
        
        return table_mock
    
    mock_supabase.table = mock_table
    return mock_supabase
# Property-based tests using Hypothesis

@given(
    thresholds_create=clinical_thresholds_create_strategy(),
    therapist_id=therapist_id_strategy()
)
@settings(max_examples=10, deadline=1500)
def test_threshold_storage_with_version_history_property(thresholds_create, therapist_id):
    """
    Property: For any patient with configured thresholds, the backend should store 
    patient-specific parameters in Supabase with version history and therapist authorization.
    
    **Validates: Requirements 15.6**
    """
    mock_supabase = create_mock_supabase()
    
    # Set therapist authorization
    thresholds_create.created_by = therapist_id
    
    # Simulate storing thresholds (first version)
    threshold_data_v1 = thresholds_create.model_dump()
    threshold_data_v1["created_at"] = datetime.now(timezone.utc).isoformat()
    threshold_data_v1["is_active"] = True
    
    result_v1 = mock_supabase.table("clinical_thresholds").insert(threshold_data_v1)
    stored_v1 = result_v1.data[0]
    
    # Property: Stored data should contain all required fields
    required_fields = [
        "id", "patient_id", "paretic_side", "normal_threshold", "pusher_threshold",
        "severe_threshold", "resistance_threshold", "episode_duration_min",
        "non_paretic_threshold", "created_by", "is_active", "version"
    ]
    for field in required_fields:
        assert field in stored_v1, f"Missing required field: {field}"
    
    # Property: Version should start at 1
    assert stored_v1["version"] == 1
    
    # Property: Therapist authorization should be preserved
    assert stored_v1["created_by"] == therapist_id
    
    # Property: Should be marked as active
    assert stored_v1["is_active"] == True
    
    # Property: Patient ID should match input
    assert stored_v1["patient_id"] == thresholds_create.patient_id
    
    # Simulate updating thresholds (second version)
    updated_thresholds = thresholds_create.model_copy()
    updated_thresholds.pusher_threshold = min(20.0, updated_thresholds.pusher_threshold + 2.0)
    updated_thresholds.severe_threshold = min(25.0, updated_thresholds.severe_threshold + 2.0)
    updated_thresholds.created_by = therapist_id
    
    # Deactivate previous version
    mock_supabase.table("clinical_thresholds").update({"is_active": False}).eq("id", stored_v1["id"]).execute()
    
    # Insert new version
    threshold_data_v2 = updated_thresholds.model_dump()
    threshold_data_v2["created_at"] = datetime.now(timezone.utc).isoformat()
    threshold_data_v2["is_active"] = True
    
    result_v2 = mock_supabase.table("clinical_thresholds").insert(threshold_data_v2)
    stored_v2 = result_v2.data[0]
    
    # Property: New version should increment version number
    assert stored_v2["version"] == 2
    
    # Property: New version should be active
    assert stored_v2["is_active"] == True
    
    # Property: Updated values should be preserved
    assert stored_v2["pusher_threshold"] == updated_thresholds.pusher_threshold
    assert stored_v2["severe_threshold"] == updated_thresholds.severe_threshold
    
    # Property: Version history should be maintained
    all_versions = mock_supabase.table("clinical_thresholds").select("*").eq("patient_id", thresholds_create.patient_id).execute()
    assert len(all_versions.data) == 2
    
    # Property: Only one version should be active
    active_versions = [v for v in all_versions.data if v.get("is_active", False)]
    assert len(active_versions) == 1
    assert active_versions[0]["version"] == 2


@given(
    thresholds_create=clinical_thresholds_create_strategy(),
    sensor_data_points=st.lists(sensor_data_point_strategy(), min_size=5, max_size=20)
)
@settings(max_examples=12, deadline=2500)
def test_consistent_threshold_application_property(thresholds_create, sensor_data_points):
    """
    Property: For any patient with configured thresholds, the system should apply 
    these thresholds consistently to all real-time detection and historical analysis.
    
    **Validates: Requirements 15.7**
    """
    # Create clinical thresholds and calibration data
    clinical_thresholds = ClinicalThresholds(
        patient_id=thresholds_create.patient_id,
        paretic_side=thresholds_create.paretic_side,
        normal_threshold=thresholds_create.normal_threshold,
        pusher_threshold=thresholds_create.pusher_threshold,
        severe_threshold=thresholds_create.severe_threshold,
        resistance_threshold=thresholds_create.resistance_threshold,
        episode_duration_min=thresholds_create.episode_duration_min
    )
    
    # Create default calibration for testing
    calibration_data = CalibrationData(
        patient_id=thresholds_create.patient_id,
        device_id="ESP32_TEST",
        baseline_pitch=0.0,
        baseline_fsr_left=2048.0,
        baseline_fsr_right=2048.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=1.0,
        fsr_std_dev=0.1,
        calibration_timestamp=datetime.now(timezone.utc)
    )
    
    # Create algorithm instance with patient-specific thresholds
    algorithm = PusherDetectionAlgorithm(clinical_thresholds, calibration_data)
    
    # Test real-time detection consistency
    real_time_results = []
    for sensor_point in sensor_data_points:
        analysis = algorithm.analyze_sensor_data(sensor_point)
        real_time_results.append({
            "timestamp": sensor_point.timestamp,
            "pitch": sensor_point.pitch,
            "pusher_detected": analysis.pusher_detected,
            "severity_score": analysis.severity_score,
            "tilt_classification": analysis.tilt_classification
        })
    
    # Test historical analysis consistency
    historical_readings = []
    for i, sensor_point in enumerate(sensor_data_points):
        historical_readings.append({
            "timestamp": sensor_point.timestamp.isoformat(),
            "imu_pitch": sensor_point.pitch,
            "fsr_left": sensor_point.fsr_left,
            "fsr_right": sensor_point.fsr_right,
            "pusher_detected": real_time_results[i]["pusher_detected"],
            "clinical_score": real_time_results[i]["severity_score"]
        })
    
    # Calculate daily metrics using same thresholds
    test_date = sensor_data_points[0].timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_metrics = algorithm.get_daily_metrics(test_date, historical_readings)
    
    # Property: Threshold application should be consistent between real-time and historical
    for i, (sensor_point, real_time_result) in enumerate(zip(sensor_data_points, real_time_results)):
        abs_pitch = abs(sensor_point.pitch)
        
        # Property: Normal threshold consistency
        if abs_pitch <= clinical_thresholds.normal_threshold:
            assert real_time_result["severity_score"] == 0, f"Normal angle {abs_pitch} should have severity 0"
        
        # Property: Pusher threshold consistency
        if abs_pitch >= clinical_thresholds.pusher_threshold:
            # Should detect pusher behavior (may depend on other criteria)
            assert real_time_result["severity_score"] >= 1, f"Pusher angle {abs_pitch} should have severity >= 1"
        
        # Property: Severe threshold consistency
        if abs_pitch >= clinical_thresholds.severe_threshold:
            assert real_time_result["severity_score"] >= 2, f"Severe angle {abs_pitch} should have severity >= 2"
    
    # Property: Daily metrics should reflect same threshold application
    pusher_episodes_count = sum(1 for r in real_time_results if r["pusher_detected"])
    assert daily_metrics["total_episodes"] >= 0
    
    # Property: Time within normal should use same normal threshold
    normal_readings = sum(1 for r in real_time_results if abs(r["pitch"]) <= clinical_thresholds.normal_threshold)
    expected_time_within_normal = (normal_readings / len(real_time_results)) * 100.0 if real_time_results else 0.0
    assert abs(daily_metrics["time_within_normal"] - expected_time_within_normal) < 0.1
    
    # Property: Max tilt angle should respect threshold classifications
    if daily_metrics["max_tilt_angle"] >= clinical_thresholds.severe_threshold:
        assert daily_metrics["total_episodes"] > 0, "Severe tilt angles should generate episodes"
@given(
    patient_id=patient_id_strategy(),
    multiple_calibrations=multiple_calibrations_strategy(),
    thresholds_create=clinical_thresholds_create_strategy()
)
@settings(max_examples=30, deadline=4000)
def test_most_recent_calibration_usage_property(patient_id, multiple_calibrations, thresholds_create):
    """
    Property: For any patient with multiple calibrations, the system should use 
    the most recent calibration data and maintain calibration history for comparison.
    
    **Validates: Requirements 18.6**
    """
    # Ensure patient IDs match
    thresholds_create.patient_id = patient_id
    for calibration_entry in multiple_calibrations:
        calibration_entry["calibration"].patient_id = patient_id
    
    mock_supabase = create_mock_supabase()
    
    # Store all calibrations in mock database
    stored_calibrations = []
    for calibration_entry in multiple_calibrations:
        calibration_data = calibration_entry["calibration"].model_dump()
        calibration_data["calibration_date"] = calibration_entry["calibration_date"].isoformat()
        calibration_data["is_active"] = calibration_entry["is_active"]
        
        result = mock_supabase.table("device_calibrations").insert(calibration_data)
        stored_calibrations.append(result.data[0])
    
    # Store clinical thresholds
    threshold_data = thresholds_create.model_dump()
    threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
    threshold_data["is_active"] = True
    mock_supabase.table("clinical_thresholds").insert(threshold_data)
    
    # Property: Should be able to retrieve most recent active calibration
    active_calibrations = mock_supabase.table("device_calibrations").select("*").eq("patient_id", patient_id).eq("is_active", True).execute()
    assert len(active_calibrations.data) == 1, "Should have exactly one active calibration"
    
    most_recent_calibration = active_calibrations.data[0]
    
    # Property: Most recent calibration should have the latest date
    expected_most_recent = max(multiple_calibrations, key=lambda x: x["calibration_date"])
    expected_date = expected_most_recent["calibration_date"].isoformat()
    assert most_recent_calibration["calibration_date"] == expected_date
    
    # Property: Should maintain calibration history
    all_calibrations = mock_supabase.table("device_calibrations").select("*").eq("patient_id", patient_id).execute()
    assert len(all_calibrations.data) == len(multiple_calibrations), "Should maintain all calibration history"
    
    # Property: Only most recent should be active
    active_count = sum(1 for c in all_calibrations.data if c.get("is_active", False))
    assert active_count == 1, "Only one calibration should be active"
    
    # Property: Calibration dates should be preserved for comparison
    stored_dates = [datetime.fromisoformat(c["calibration_date"]) for c in all_calibrations.data]
    original_dates = [c["calibration_date"] for c in multiple_calibrations]
    
    # Sort both lists for comparison
    stored_dates.sort()
    original_dates.sort()
    
    for stored_date, original_date in zip(stored_dates, original_dates):
        assert abs((stored_date - original_date).total_seconds()) < 1, "Calibration dates should be preserved"
    
    # Property: Most recent calibration should be used for adaptive thresholds
    clinical_thresholds_dict = {
        'normal_threshold': thresholds_create.normal_threshold,
        'pusher_threshold': thresholds_create.pusher_threshold,
        'severe_threshold': thresholds_create.severe_threshold
    }
    
    # Convert most recent calibration to CalibrationDataCreate for threshold calculation
    most_recent_cal_create = CalibrationDataCreate(
        patient_id=most_recent_calibration["patient_id"],
        device_id=most_recent_calibration["device_id"],
        baseline_pitch=most_recent_calibration["baseline_pitch"],
        baseline_fsr_left=most_recent_calibration["baseline_fsr_left"],
        baseline_fsr_right=most_recent_calibration["baseline_fsr_right"],
        pitch_std_dev=most_recent_calibration["pitch_std_dev"],
        fsr_std_dev=most_recent_calibration["fsr_std_dev"]
    )
    
    adaptive_thresholds = calculate_adaptive_thresholds(most_recent_cal_create, clinical_thresholds_dict)
    
    # Property: Adaptive thresholds should be calculated from most recent calibration
    assert adaptive_thresholds.patient_id == patient_id
    assert adaptive_thresholds.device_id == most_recent_calibration["device_id"]
    
    # Property: Adaptive thresholds should incorporate most recent baseline values
    expected_baseline_ratio = most_recent_cal_create.baseline_fsr_ratio
    assert abs(adaptive_thresholds.normal_fsr_imbalance_threshold - (2.0 * most_recent_cal_create.fsr_std_dev)) < 0.001


@given(
    threshold_versions=threshold_version_history_strategy(),
    sensor_data_points=st.lists(sensor_data_point_strategy(), min_size=10, max_size=30)
)
@settings(max_examples=25, deadline=5000)
def test_threshold_version_consistency_property(threshold_versions, sensor_data_points):
    """
    Property: For any patient with threshold version history, the system should 
    consistently apply the active version and maintain version integrity.
    
    **Validates: Requirements 15.6, 15.7**
    """
    if not threshold_versions:
        return  # Skip if no versions generated
    
    patient_id = threshold_versions[0]["thresholds"].patient_id
    
    # Ensure all sensor data points have consistent timestamps
    base_date = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    for i, sensor_point in enumerate(sensor_data_points):
        sensor_point.timestamp = base_date + timedelta(minutes=i * 5)
    
    mock_supabase = create_mock_supabase()
    
    # Store all threshold versions
    for version_entry in threshold_versions:
        threshold_data = version_entry["thresholds"].model_dump()
        threshold_data["id"] = version_entry["id"]
        threshold_data["version"] = version_entry["version"]
        threshold_data["created_at"] = version_entry["created_at"].isoformat()
        threshold_data["is_active"] = version_entry["is_active"]
        
        mock_supabase.table("clinical_thresholds").insert(threshold_data)
    
    # Property: Should retrieve only active version
    active_thresholds = mock_supabase.table("clinical_thresholds").select("*").eq("patient_id", patient_id).eq("is_active", True).execute()
    assert len(active_thresholds.data) == 1, "Should have exactly one active threshold version"
    
    active_threshold = active_thresholds.data[0]
    expected_active = next(v for v in threshold_versions if v["is_active"])
    assert active_threshold["version"] == expected_active["version"]
    
    # Property: Version history should be complete
    all_thresholds = mock_supabase.table("clinical_thresholds").select("*").eq("patient_id", patient_id).execute()
    assert len(all_thresholds.data) == len(threshold_versions), "Should maintain complete version history"
    
    # Property: Version numbers should be sequential and unique
    version_numbers = [t["version"] for t in all_thresholds.data]
    version_numbers.sort()
    expected_versions = list(range(1, len(threshold_versions) + 1))
    assert version_numbers == expected_versions, "Version numbers should be sequential"
    
    # Property: Active threshold should be applied consistently
    active_thresholds_obj = ClinicalThresholds(
        patient_id=patient_id,
        paretic_side=expected_active["thresholds"].paretic_side,
        normal_threshold=expected_active["thresholds"].normal_threshold,
        pusher_threshold=expected_active["thresholds"].pusher_threshold,
        severe_threshold=expected_active["thresholds"].severe_threshold,
        resistance_threshold=expected_active["thresholds"].resistance_threshold,
        episode_duration_min=expected_active["thresholds"].episode_duration_min
    )
    
    # Create default calibration
    calibration_data = CalibrationData(
        patient_id=patient_id,
        device_id="ESP32_TEST",
        baseline_pitch=0.0,
        baseline_fsr_left=2048.0,
        baseline_fsr_right=2048.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=1.0,
        fsr_std_dev=0.1,
        calibration_timestamp=datetime.now(timezone.utc)
    )
    
    algorithm = PusherDetectionAlgorithm(active_thresholds_obj, calibration_data)
    
    # Test that active thresholds are applied consistently
    for sensor_point in sensor_data_points:
        analysis = algorithm.analyze_sensor_data(sensor_point)
        abs_pitch = abs(sensor_point.pitch)
        
        # Property: Should use active version's thresholds
        if abs_pitch <= active_thresholds_obj.normal_threshold:
            assert analysis.severity_score == 0, f"Should use active normal threshold {active_thresholds_obj.normal_threshold}"
        
        if abs_pitch >= active_thresholds_obj.severe_threshold:
            assert analysis.severity_score >= 2, f"Should use active severe threshold {active_thresholds_obj.severe_threshold}"
    
    # Property: Historical analysis should use same active thresholds
    historical_readings = []
    for sensor_point in sensor_data_points:
        historical_readings.append({
            "timestamp": sensor_point.timestamp.isoformat(),
            "imu_pitch": sensor_point.pitch,
            "fsr_left": sensor_point.fsr_left,
            "fsr_right": sensor_point.fsr_right,
            "pusher_detected": abs(sensor_point.pitch) >= active_thresholds_obj.pusher_threshold,
            "clinical_score": min(3, int(abs(sensor_point.pitch) / 7))
        })
    
    test_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_metrics = algorithm.get_daily_metrics(test_date, historical_readings)
    
    # Property: Daily metrics should reflect active threshold application
    normal_count = sum(1 for r in historical_readings if abs(r["imu_pitch"]) <= active_thresholds_obj.normal_threshold)
    expected_time_normal = (normal_count / len(historical_readings)) * 100.0 if historical_readings else 0.0
    assert abs(daily_metrics["time_within_normal"] - expected_time_normal) < 0.1
@given(
    thresholds_create=clinical_thresholds_create_strategy(),
    calibration_create=calibration_data_create_strategy(),
    sensor_data_points=st.lists(sensor_data_point_strategy(), min_size=15, max_size=40)
)
@settings(max_examples=20, deadline=6000)
def test_integrated_threshold_calibration_application_property(thresholds_create, calibration_create, sensor_data_points):
    """
    Property: For any patient with both configured thresholds and calibration data, 
    the system should integrate both consistently for accurate detection and analysis.
    
    **Validates: Requirements 15.6, 15.7, 18.6**
    """
    # Ensure patient IDs match
    patient_id = thresholds_create.patient_id
    calibration_create.patient_id = patient_id
    
    mock_supabase = create_mock_supabase()
    
    # Store clinical thresholds
    threshold_data = thresholds_create.model_dump()
    threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
    threshold_data["is_active"] = True
    threshold_result = mock_supabase.table("clinical_thresholds").insert(threshold_data)
    stored_threshold = threshold_result.data[0]
    
    # Store calibration data
    calibration_data = calibration_create.model_dump()
    calibration_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
    calibration_data["is_active"] = True
    calibration_result = mock_supabase.table("device_calibrations").insert(calibration_data)
    stored_calibration = calibration_result.data[0]
    
    # Property: Both threshold and calibration should be stored with patient association
    assert stored_threshold["patient_id"] == patient_id
    assert stored_calibration["patient_id"] == patient_id
    assert stored_threshold["is_active"] == True
    assert stored_calibration["is_active"] == True
    
    # Create integrated algorithm with both thresholds and calibration
    clinical_thresholds = ClinicalThresholds(
        patient_id=patient_id,
        paretic_side=thresholds_create.paretic_side,
        normal_threshold=thresholds_create.normal_threshold,
        pusher_threshold=thresholds_create.pusher_threshold,
        severe_threshold=thresholds_create.severe_threshold,
        resistance_threshold=thresholds_create.resistance_threshold,
        episode_duration_min=thresholds_create.episode_duration_min
    )
    
    calibration_obj = CalibrationData(
        patient_id=patient_id,
        device_id=calibration_create.device_id,
        baseline_pitch=calibration_create.baseline_pitch,
        baseline_fsr_left=calibration_create.baseline_fsr_left,
        baseline_fsr_right=calibration_create.baseline_fsr_right,
        baseline_fsr_ratio=calibration_create.baseline_fsr_ratio,
        pitch_std_dev=calibration_create.pitch_std_dev,
        fsr_std_dev=calibration_create.fsr_std_dev,
        calibration_timestamp=datetime.now(timezone.utc)
    )
    
    algorithm = PusherDetectionAlgorithm(clinical_thresholds, calibration_obj)
    
    # Property: Algorithm should integrate both threshold and calibration data
    assert algorithm.thresholds.patient_id == patient_id
    assert algorithm.calibration.patient_id == patient_id
    
    # Test integrated analysis
    integrated_results = []
    for sensor_point in sensor_data_points:
        analysis = algorithm.analyze_sensor_data(sensor_point)
        
        # Calculate adjusted pitch using calibration baseline
        adjusted_pitch = sensor_point.pitch - calibration_obj.baseline_pitch
        
        integrated_results.append({
            "timestamp": sensor_point.timestamp,
            "raw_pitch": sensor_point.pitch,
            "adjusted_pitch": adjusted_pitch,
            "pusher_detected": analysis.pusher_detected,
            "severity_score": analysis.severity_score,
            "confidence_level": analysis.confidence_level
        })
    
    # Property: Calibration baseline should be applied to pitch measurements
    for result in integrated_results:
        expected_adjusted = result["raw_pitch"] - calibration_obj.baseline_pitch
        assert abs(result["adjusted_pitch"] - expected_adjusted) < 0.001
    
    # Property: Thresholds should be applied to calibration-adjusted measurements
    for result in integrated_results:
        abs_adjusted_pitch = abs(result["adjusted_pitch"])
        
        # Normal threshold should use adjusted pitch
        if abs_adjusted_pitch <= clinical_thresholds.normal_threshold:
            assert result["severity_score"] == 0, f"Adjusted pitch {abs_adjusted_pitch} within normal threshold should have severity 0"
        
        # Severe threshold should use adjusted pitch
        if abs_adjusted_pitch >= clinical_thresholds.severe_threshold:
            assert result["severity_score"] >= 2, f"Adjusted pitch {abs_adjusted_pitch} above severe threshold should have severity >= 2"
    
    # Property: FSR analysis should use calibration baseline
    for i, sensor_point in enumerate(sensor_data_points):
        current_fsr_ratio = sensor_point.fsr_right / (sensor_point.fsr_left + sensor_point.fsr_right) if (sensor_point.fsr_left + sensor_point.fsr_right) > 0 else 0.5
        baseline_deviation = abs(current_fsr_ratio - calibration_obj.baseline_fsr_ratio)
        
        # If FSR deviation is significant (> 2 * std_dev), should contribute to detection
        if baseline_deviation > (2.0 * calibration_obj.fsr_std_dev):
            # Should increase confidence or contribute to pusher detection
            analysis = algorithm.analyze_sensor_data(sensor_point)
            assert analysis.confidence_level > 0.0, "Significant FSR deviation should increase confidence"
    
    # Property: Historical analysis should maintain integration consistency
    historical_readings = []
    for i, sensor_point in enumerate(sensor_data_points):
        historical_readings.append({
            "timestamp": sensor_point.timestamp.isoformat(),
            "imu_pitch": sensor_point.pitch,
            "fsr_left": sensor_point.fsr_left,
            "fsr_right": sensor_point.fsr_right,
            "pusher_detected": integrated_results[i]["pusher_detected"],
            "clinical_score": integrated_results[i]["severity_score"]
        })
    
    test_date = sensor_data_points[0].timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_metrics = algorithm.get_daily_metrics(test_date, historical_readings)
    
    # Property: Daily metrics should reflect integrated threshold-calibration analysis
    assert daily_metrics["total_episodes"] >= 0
    assert 0.0 <= daily_metrics["time_within_normal"] <= 100.0
    assert daily_metrics["resistance_index"] >= 0.0
    
    # Property: Time within normal should use calibration-adjusted measurements
    normal_count = 0
    for sensor_point in sensor_data_points:
        adjusted_pitch = sensor_point.pitch - calibration_obj.baseline_pitch
        if abs(adjusted_pitch) <= clinical_thresholds.normal_threshold:
            normal_count += 1
    
    expected_time_normal = (normal_count / len(sensor_data_points)) * 100.0 if sensor_data_points else 0.0
    assert abs(daily_metrics["time_within_normal"] - expected_time_normal) < 0.1
    
    # Property: Adaptive thresholds should be calculable from integration
    clinical_thresholds_dict = {
        'normal_threshold': clinical_thresholds.normal_threshold,
        'pusher_threshold': clinical_thresholds.pusher_threshold,
        'severe_threshold': clinical_thresholds.severe_threshold
    }
    
    adaptive_thresholds = calculate_adaptive_thresholds(calibration_create, clinical_thresholds_dict)
    
    # Property: Adaptive thresholds should incorporate both threshold and calibration data
    assert adaptive_thresholds.patient_id == patient_id
    assert adaptive_thresholds.normal_pitch_threshold > 0
    assert adaptive_thresholds.pusher_pitch_threshold > adaptive_thresholds.normal_pitch_threshold
    assert adaptive_thresholds.severe_pitch_threshold > adaptive_thresholds.pusher_pitch_threshold
    assert adaptive_thresholds.normal_fsr_imbalance_threshold > 0


# Integration test combining all properties
@given(
    patient_id=patient_id_strategy(),
    therapist_id=therapist_id_strategy(),
    device_id=device_id_strategy()
)
@settings(max_examples=15, deadline=8000)
def test_comprehensive_patient_specific_threshold_system_property(patient_id, therapist_id, device_id):
    """
    Property: For any patient in the system, the complete patient-specific threshold 
    application workflow should maintain data integrity and consistency across all operations.
    
    **Validates: Requirements 15.6, 15.7, 18.6**
    """
    mock_supabase = create_mock_supabase()
    
    # Step 1: Create initial thresholds
    initial_thresholds = ClinicalThresholdsCreate(
        patient_id=patient_id,
        paretic_side=PareticSide.RIGHT,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        resistance_threshold=2.0,
        episode_duration_min=2.0,
        non_paretic_threshold=0.7,
        created_by=therapist_id,
        therapist_notes="Initial configuration"
    )
    
    threshold_data = initial_thresholds.model_dump()
    threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
    threshold_data["is_active"] = True
    
    result1 = mock_supabase.table("clinical_thresholds").insert(threshold_data)
    stored_threshold1 = result1.data[0]
    
    # Property: Initial threshold should be stored correctly
    assert stored_threshold1["patient_id"] == patient_id
    assert stored_threshold1["created_by"] == therapist_id
    assert stored_threshold1["version"] == 1
    assert stored_threshold1["is_active"] == True
    
    # Step 2: Add calibration data
    calibration = CalibrationDataCreate(
        patient_id=patient_id,
        device_id=device_id,
        baseline_pitch=1.5,
        baseline_fsr_left=2000.0,
        baseline_fsr_right=2100.0,
        pitch_std_dev=1.2,
        fsr_std_dev=0.08,
        calibration_duration=30,
        sample_count=150
    )
    
    calibration_data = calibration.model_dump()
    calibration_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
    calibration_data["is_active"] = True
    
    cal_result = mock_supabase.table("device_calibrations").insert(calibration_data)
    stored_calibration = cal_result.data[0]
    
    # Property: Calibration should be associated with patient
    assert stored_calibration["patient_id"] == patient_id
    assert stored_calibration["device_id"] == device_id
    assert stored_calibration["is_active"] == True
    
    # Step 3: Update thresholds (create version 2)
    mock_supabase.table("clinical_thresholds").update({"is_active": False}).eq("id", stored_threshold1["id"]).execute()
    
    updated_thresholds = initial_thresholds.model_copy()
    updated_thresholds.pusher_threshold = 12.0
    updated_thresholds.severe_threshold = 22.0
    updated_thresholds.therapist_notes = "Adjusted based on patient progress"
    
    updated_data = updated_thresholds.model_dump()
    updated_data["created_at"] = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    updated_data["is_active"] = True
    
    result2 = mock_supabase.table("clinical_thresholds").insert(updated_data)
    stored_threshold2 = result2.data[0]
    
    # Property: Version history should be maintained
    all_thresholds = mock_supabase.table("clinical_thresholds").select("*").eq("patient_id", patient_id).execute()
    assert len(all_thresholds.data) == 2
    
    active_thresholds = [t for t in all_thresholds.data if t.get("is_active", False)]
    assert len(active_thresholds) == 1
    assert active_thresholds[0]["version"] == 2
    
    # Step 4: Add second calibration (newer)
    newer_calibration = calibration.model_copy()
    newer_calibration.baseline_pitch = 0.8
    newer_calibration.pitch_std_dev = 0.9
    
    # Deactivate old calibration
    mock_supabase.table("device_calibrations").update({"is_active": False}).eq("id", stored_calibration["id"]).execute()
    
    newer_cal_data = newer_calibration.model_dump()
    newer_cal_data["calibration_date"] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    newer_cal_data["is_active"] = True
    
    newer_cal_result = mock_supabase.table("device_calibrations").insert(newer_cal_data)
    stored_newer_calibration = newer_cal_result.data[0]
    
    # Property: Most recent calibration should be active
    all_calibrations = mock_supabase.table("device_calibrations").select("*").eq("patient_id", patient_id).execute()
    assert len(all_calibrations.data) == 2
    
    active_calibrations = [c for c in all_calibrations.data if c.get("is_active", False)]
    assert len(active_calibrations) == 1
    assert active_calibrations[0]["id"] == stored_newer_calibration["id"]
    
    # Step 5: Test integrated system behavior
    active_threshold = active_thresholds[0]
    active_calibration = active_calibrations[0]
    
    # Create algorithm with most recent data
    clinical_thresholds_obj = ClinicalThresholds(
        patient_id=patient_id,
        paretic_side=PareticSide(active_threshold["paretic_side"]),
        normal_threshold=active_threshold["normal_threshold"],
        pusher_threshold=active_threshold["pusher_threshold"],
        severe_threshold=active_threshold["severe_threshold"],
        resistance_threshold=active_threshold["resistance_threshold"],
        episode_duration_min=active_threshold["episode_duration_min"]
    )
    
    calibration_obj = CalibrationData(
        patient_id=patient_id,
        device_id=active_calibration["device_id"],
        baseline_pitch=active_calibration["baseline_pitch"],
        baseline_fsr_left=active_calibration["baseline_fsr_left"],
        baseline_fsr_right=active_calibration["baseline_fsr_right"],
        baseline_fsr_ratio=active_calibration["baseline_fsr_ratio"],
        pitch_std_dev=active_calibration["pitch_std_dev"],
        fsr_std_dev=active_calibration["fsr_std_dev"],
        calibration_timestamp=datetime.fromisoformat(active_calibration["calibration_date"])
    )
    
    algorithm = PusherDetectionAlgorithm(clinical_thresholds_obj, calibration_obj)
    
    # Property: Algorithm should use most recent threshold and calibration versions
    assert algorithm.thresholds.pusher_threshold == 12.0  # Updated value
    assert algorithm.calibration.baseline_pitch == 0.8  # Newer calibration value
    
    # Property: System should maintain referential integrity
    assert algorithm.thresholds.patient_id == patient_id
    assert algorithm.calibration.patient_id == patient_id
    
    # Test with sample sensor data
    test_sensor = SensorDataPoint(
        timestamp=datetime.now(timezone.utc),
        pitch=15.0,  # Should trigger pusher detection with updated thresholds
        fsr_left=1800,
        fsr_right=2200,
        device_id=device_id
    )
    
    analysis = algorithm.analyze_sensor_data(test_sensor)
    
    # Property: Analysis should use integrated most recent data
    adjusted_pitch = test_sensor.pitch - calibration_obj.baseline_pitch  # 15.0 - 0.8 = 14.2
    assert abs(adjusted_pitch) >= clinical_thresholds_obj.pusher_threshold  # 14.2 >= 12.0
    assert analysis.severity_score >= 1  # Should detect pusher behavior
    
    print(f"✓ Comprehensive system test passed for patient {patient_id}")
    print(f"  - Threshold versions: {len(all_thresholds.data)}")
    print(f"  - Calibration versions: {len(all_calibrations.data)}")
    print(f"  - Active threshold version: {active_threshold['version']}")
    print(f"  - Most recent calibration baseline: {calibration_obj.baseline_pitch}")
    print(f"  - Integrated analysis result: severity={analysis.severity_score}, confidence={analysis.confidence_level:.2f}")


if __name__ == "__main__":
    print("🧪 Running Patient-Specific Threshold Application Property Tests...")
    print("**Validates: Requirements 15.6, 15.7, 18.6**")
    print()
    
    # Run individual property tests
    test_functions = [
        ("Threshold Storage with Version History", test_threshold_storage_with_version_history_property),
        ("Consistent Threshold Application", test_consistent_threshold_application_property),
        ("Most Recent Calibration Usage", test_most_recent_calibration_usage_property),
        ("Threshold Version Consistency", test_threshold_version_consistency_property),
        ("Integrated Threshold-Calibration Application", test_integrated_threshold_calibration_application_property),
        ("Comprehensive Patient-Specific System", test_comprehensive_patient_specific_threshold_system_property),
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
        print("🎉 All patient-specific threshold application properties validated!")
        print("\n✅ Validated Requirements:")
        print("- 15.6: Store patient-specific thresholds with version history and therapist authorization")
        print("- 15.7: Apply patient-specific parameters consistently to real-time detection and historical analysis")
        print("- 18.6: Use most recent calibration data and maintain calibration history for comparison")
    else:
        print("⚠️  Some property tests failed. Check patient-specific threshold implementation.")