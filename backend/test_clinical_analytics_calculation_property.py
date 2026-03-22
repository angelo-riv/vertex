#!/usr/bin/env python3
"""
Property-Based Test for Clinical Analytics Calculation

**Validates: Requirements 14.4, 14.5, 14.7**

Property 12: Clinical Analytics Calculation
For any daily patient data, the system should calculate episode frequency, 
mean/maximum tilt angles during episodes, resistance index during correction attempts, 
time spent within ±5° of vertical, and generate weekly progress reports showing trends 
in episode frequency, tilt improvements, and resistance reduction.

This test validates that the clinical analytics calculations are mathematically correct 
and consistent across all input scenarios.
"""

import pytest
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from clinical_algorithm import (
    PusherDetectionAlgorithm, 
    ClinicalThresholds, 
    CalibrationData, 
    PareticSide,
    SeverityScore,
    TiltClassification
)


# Test configuration
NORMAL_THRESHOLD = 5.0  # ±5° of vertical
PUSHER_THRESHOLD = 10.0  # ≥10° for pusher detection
SEVERE_THRESHOLD = 20.0  # ≥20° for severe episodes
EXPECTED_CORRECTION_IMPROVEMENT = 5.0  # Expected 5° improvement during correction


# Hypothesis strategies for generating test data
@st.composite
def clinical_thresholds_strategy(draw):
    """Generate valid clinical thresholds for property testing"""
    paretic_side = draw(st.sampled_from([PareticSide.LEFT, PareticSide.RIGHT]))
    normal_threshold = draw(st.floats(min_value=3.0, max_value=7.0))
    pusher_threshold = draw(st.floats(min_value=8.0, max_value=15.0))
    severe_threshold = draw(st.floats(min_value=18.0, max_value=25.0))
    
    return ClinicalThresholds(
        patient_id="test_patient",
        paretic_side=paretic_side,
        normal_threshold=normal_threshold,
        pusher_threshold=pusher_threshold,
        severe_threshold=severe_threshold,
        resistance_threshold=2.0,
        episode_duration_min=2.0
    )


@st.composite
def calibration_data_strategy(draw):
    """Generate valid calibration data for property testing"""
    baseline_pitch = draw(st.floats(min_value=-5.0, max_value=5.0))
    baseline_fsr_ratio = draw(st.floats(min_value=0.3, max_value=0.7))
    pitch_std_dev = draw(st.floats(min_value=0.5, max_value=3.0))
    fsr_std_dev = draw(st.floats(min_value=0.05, max_value=0.2))
    
    return CalibrationData(
        patient_id="test_patient",
        device_id="ESP32_TEST",
        baseline_pitch=baseline_pitch,
        baseline_fsr_left=2048 * (1 - baseline_fsr_ratio),
        baseline_fsr_right=2048 * baseline_fsr_ratio,
        baseline_fsr_ratio=baseline_fsr_ratio,
        pitch_std_dev=pitch_std_dev,
        fsr_std_dev=fsr_std_dev,
        calibration_timestamp=datetime.now(timezone.utc)
    )


@st.composite
def sensor_reading_strategy(draw):
    """Generate sensor reading data for analytics testing"""
    timestamp = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    )).replace(tzinfo=timezone.utc)
    
    pitch = draw(st.floats(min_value=-30.0, max_value=30.0, allow_nan=False, allow_infinity=False))
    fsr_left = draw(st.integers(min_value=0, max_value=4095))
    fsr_right = draw(st.integers(min_value=0, max_value=4095))
    pusher_detected = draw(st.booleans())
    clinical_score = draw(st.integers(min_value=0, max_value=3))
    correction_attempt = draw(st.booleans())
    
    return {
        "timestamp": timestamp.isoformat(),
        "imu_pitch": pitch,
        "fsr_left": fsr_left,
        "fsr_right": fsr_right,
        "pusher_detected": pusher_detected,
        "clinical_score": clinical_score,
        "correction_attempt": correction_attempt,
        "initial_angle": pitch if correction_attempt else None,
        "final_angle": pitch - draw(st.floats(min_value=-2.0, max_value=8.0)) if correction_attempt else None
    }


@st.composite
def daily_sensor_readings_strategy(draw):
    """Generate a day's worth of sensor readings for analytics testing"""
    base_date = draw(st.dates(min_value=datetime(2024, 1, 1).date(), max_value=datetime(2024, 12, 31).date()))
    reading_count = draw(st.integers(min_value=10, max_value=100))
    
    readings = []
    for i in range(reading_count):
        # Distribute readings throughout the day
        hour = draw(st.integers(min_value=8, max_value=20))  # Active hours 8 AM to 8 PM
        minute = draw(st.integers(min_value=0, max_value=59))
        second = draw(st.integers(min_value=0, max_value=59))
        
        timestamp = datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        pitch = draw(st.floats(min_value=-30.0, max_value=30.0, allow_nan=False, allow_infinity=False))
        fsr_left = draw(st.integers(min_value=0, max_value=4095))
        fsr_right = draw(st.integers(min_value=0, max_value=4095))
        
        # Generate pusher episodes with some correlation to tilt angle
        pusher_detected = abs(pitch) >= PUSHER_THRESHOLD and draw(st.booleans())
        clinical_score = min(3, int(abs(pitch) / 7)) if pusher_detected else 0
        correction_attempt = pusher_detected and draw(st.floats(min_value=0.0, max_value=1.0)) < 0.3  # 30% chance
        
        reading = {
            "timestamp": timestamp.isoformat(),
            "imu_pitch": pitch,
            "fsr_left": fsr_left,
            "fsr_right": fsr_right,
            "pusher_detected": pusher_detected,
            "clinical_score": clinical_score,
            "correction_attempt": correction_attempt
        }
        
        if correction_attempt:
            # Add correction attempt data
            improvement = draw(st.floats(min_value=-2.0, max_value=8.0))
            reading["initial_angle"] = pitch
            reading["final_angle"] = pitch - improvement
        
        readings.append(reading)
    
    # Sort by timestamp
    readings.sort(key=lambda x: x["timestamp"])
    return readings


@st.composite
def weekly_sensor_readings_strategy(draw):
    """Generate a week's worth of sensor readings for weekly analytics testing"""
    base_date = draw(st.dates(min_value=datetime(2024, 1, 7).date(), max_value=datetime(2024, 12, 24).date()))
    
    weekly_readings = []
    for day_offset in range(7):
        day_date = base_date + timedelta(days=day_offset)
        daily_reading_count = draw(st.integers(min_value=5, max_value=50))
        
        for i in range(daily_reading_count):
            hour = draw(st.integers(min_value=8, max_value=20))
            minute = draw(st.integers(min_value=0, max_value=59))
            second = draw(st.integers(min_value=0, max_value=59))
            
            timestamp = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=minute, second=second))
            timestamp = timestamp.replace(tzinfo=timezone.utc)
            
            pitch = draw(st.floats(min_value=-30.0, max_value=30.0, allow_nan=False, allow_infinity=False))
            fsr_left = draw(st.integers(min_value=0, max_value=4095))
            fsr_right = draw(st.integers(min_value=0, max_value=4095))
            
            pusher_detected = abs(pitch) >= PUSHER_THRESHOLD and draw(st.booleans())
            clinical_score = min(3, int(abs(pitch) / 7)) if pusher_detected else 0
            correction_attempt = pusher_detected and draw(st.floats(min_value=0.0, max_value=1.0)) < 0.2
            
            reading = {
                "timestamp": timestamp.isoformat(),
                "imu_pitch": pitch,
                "fsr_left": fsr_left,
                "fsr_right": fsr_right,
                "pusher_detected": pusher_detected,
                "clinical_score": clinical_score,
                "correction_attempt": correction_attempt
            }
            
            if correction_attempt:
                improvement = draw(st.floats(min_value=-2.0, max_value=8.0))
                reading["initial_angle"] = pitch
                reading["final_angle"] = pitch - improvement
            
            weekly_readings.append(reading)
    
    weekly_readings.sort(key=lambda x: x["timestamp"])
    # Convert end_date to datetime object for compatibility with the algorithm
    end_datetime = datetime.combine(base_date + timedelta(days=6), datetime.min.time()).replace(tzinfo=timezone.utc)
    return weekly_readings, end_datetime  # Return readings and end datetime

# Property-based tests using Hypothesis

@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    daily_readings=daily_sensor_readings_strategy()
)
@settings(max_examples=15, deadline=2000)
def test_daily_metrics_calculation_property(thresholds, calibration, daily_readings):
    """
    Property: For any daily patient data, the system should calculate episode frequency, 
    mean/maximum tilt angles during episodes, resistance index during correction attempts, 
    and time spent within ±5° of vertical correctly.
    
    **Validates: Requirements 14.4**
    """
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Extract date from first reading
    first_timestamp = datetime.fromisoformat(daily_readings[0]["timestamp"])
    test_date = first_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate daily metrics
    metrics = algorithm.get_daily_metrics(test_date, daily_readings)
    
    # Property: Metrics should contain all required fields
    required_fields = [
        "date", "total_episodes", "mean_tilt_angle", "max_tilt_angle",
        "time_within_normal", "resistance_index", "correction_attempts", "episodes_detail"
    ]
    for field in required_fields:
        assert field in metrics, f"Missing required field: {field}"
    
    # Property: Date should match input date
    expected_date = test_date.date().isoformat()
    assert metrics["date"] == expected_date
    
    # Property: Episode count should be non-negative
    assert metrics["total_episodes"] >= 0
    assert isinstance(metrics["total_episodes"], int)
    
    # Property: Tilt angles should be within valid ranges
    assert 0.0 <= metrics["mean_tilt_angle"] <= 180.0
    assert 0.0 <= metrics["max_tilt_angle"] <= 180.0
    
    # Property: Time within normal should be percentage (0-100)
    assert 0.0 <= metrics["time_within_normal"] <= 100.0
    
    # Property: Resistance index should be non-negative (can exceed 1.0 if corrections worsen tilt)
    assert metrics["resistance_index"] >= 0.0
    
    # Property: Correction attempts should be non-negative
    assert metrics["correction_attempts"] >= 0
    assert isinstance(metrics["correction_attempts"], int)
    
    # Property: Episodes detail should be a list
    assert isinstance(metrics["episodes_detail"], list)
    assert len(metrics["episodes_detail"]) == metrics["total_episodes"]
    
    # Verify manual calculation of time within normal
    normal_readings = sum(1 for r in daily_readings if abs(r["imu_pitch"]) <= NORMAL_THRESHOLD)
    expected_time_within_normal = (normal_readings / len(daily_readings)) * 100.0 if daily_readings else 0.0
    assert abs(metrics["time_within_normal"] - expected_time_within_normal) < 0.1
    
    # Verify manual calculation of correction attempts
    expected_correction_attempts = sum(1 for r in daily_readings if r.get("correction_attempt", False))
    assert metrics["correction_attempts"] == expected_correction_attempts
    
    # Property: If no pusher episodes detected, mean and max tilt should be 0
    pusher_readings = [r for r in daily_readings if r.get("pusher_detected", False)]
    if not pusher_readings:
        assert metrics["mean_tilt_angle"] == 0.0
        assert metrics["max_tilt_angle"] == 0.0
    
    # Property: Max tilt should be >= mean tilt
    if metrics["total_episodes"] > 0:
        assert metrics["max_tilt_angle"] >= metrics["mean_tilt_angle"]


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    weekly_data=weekly_sensor_readings_strategy()
)
@settings(max_examples=10, deadline=3000)
def test_weekly_progress_report_property(thresholds, calibration, weekly_data):
    """
    Property: For any weekly patient data, the system should generate weekly progress 
    reports showing trends in episode frequency, tilt improvements, and resistance reduction.
    
    **Validates: Requirements 14.5, 14.7**
    """
    weekly_readings, end_date = weekly_data
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Generate weekly progress report
    report = algorithm.get_weekly_progress_report(end_date, weekly_readings)
    
    # Property: Report should contain all required sections
    required_sections = ["report_period", "weekly_summary", "trend_analysis", "clinical_assessment", "daily_breakdown"]
    for section in required_sections:
        assert section in report, f"Missing required section: {section}"
    
    # Property: Report period should be exactly 7 days
    period = report["report_period"]
    start_date_str = period["start_date"]
    end_date_str = period["end_date"]
    
    # Parse the date strings
    if isinstance(start_date_str, str):
        start_date = datetime.fromisoformat(start_date_str).date()
    else:
        start_date = start_date_str
        
    if isinstance(end_date_str, str):
        report_end_date = datetime.fromisoformat(end_date_str).date()
    else:
        report_end_date = end_date_str
    
    assert (report_end_date - start_date).days == 6  # 7-day period including both dates
    assert period["days_analyzed"] == 7
    
    # Property: Weekly summary should contain valid metrics
    summary = report["weekly_summary"]
    required_summary_fields = [
        "total_episodes", "average_daily_episodes", "average_mean_tilt", 
        "peak_tilt_angle", "average_resistance_index", "average_time_within_normal", 
        "no_pushing_percentage"
    ]
    for field in required_summary_fields:
        assert field in summary, f"Missing summary field: {field}"
    
    # Property: Summary values should be within valid ranges
    assert summary["total_episodes"] >= 0
    assert summary["average_daily_episodes"] >= 0.0
    assert 0.0 <= summary["average_mean_tilt"] <= 180.0
    assert 0.0 <= summary["peak_tilt_angle"] <= 180.0
    assert summary["average_resistance_index"] >= 0.0  # Can exceed 1.0 if corrections worsen tilt
    assert 0.0 <= summary["average_time_within_normal"] <= 100.0
    assert 0.0 <= summary["no_pushing_percentage"] <= 100.0
    
    # Property: Trend analysis should contain all trend categories
    trends = report["trend_analysis"]
    required_trends = ["episode_frequency_trend", "tilt_angle_improvement", "resistance_reduction", "normal_posture_time"]
    for trend in required_trends:
        assert trend in trends, f"Missing trend: {trend}"
        
        # Each trend should have direction, slope, and interpretation
        trend_data = trends[trend]
        assert "direction" in trend_data
        assert "slope" in trend_data
        assert "interpretation" in trend_data
        assert trend_data["direction"] in ["improving", "worsening", "stable"]
    
    # Property: Clinical assessment should contain all required fields
    assessment = report["clinical_assessment"]
    required_assessment_fields = ["overall_progress", "key_improvements", "areas_of_concern", "recommendations"]
    for field in required_assessment_fields:
        assert field in assessment, f"Missing assessment field: {field}"
    
    # Property: Daily breakdown should have 7 days
    daily_breakdown = report["daily_breakdown"]
    assert len(daily_breakdown) == 7
    
    # Property: Each daily metric should be valid
    for daily_metric in daily_breakdown:
        assert "date" in daily_metric
        assert "total_episodes" in daily_metric
        assert daily_metric["total_episodes"] >= 0
        assert 0.0 <= daily_metric["time_within_normal"] <= 100.0
    
    # Verify manual calculation of no pushing percentage
    total_readings = len(weekly_readings)
    no_pushing_readings = sum(1 for r in weekly_readings if not r.get("pusher_detected", False))
    expected_no_pushing_percentage = (no_pushing_readings / total_readings) * 100 if total_readings > 0 else 0
    assert abs(summary["no_pushing_percentage"] - expected_no_pushing_percentage) < 0.1
    
    # Property: Average daily episodes should equal total episodes / 7
    expected_avg_daily = summary["total_episodes"] / 7.0
    assert abs(summary["average_daily_episodes"] - expected_avg_daily) < 0.1


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    readings=st.lists(sensor_reading_strategy(), min_size=5, max_size=20)
)
@settings(max_examples=40, deadline=2000)
def test_episode_calculation_consistency_property(thresholds, calibration, readings):
    """
    Property: For any set of sensor readings, episode calculation should be consistent 
    and mathematically correct.
    
    **Validates: Requirements 14.4, 14.7**
    """
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Sort readings by timestamp
    sorted_readings = sorted(readings, key=lambda x: x["timestamp"])
    
    # Calculate episodes using the algorithm's internal method
    episodes = algorithm._calculate_daily_episodes(sorted_readings)
    
    # Property: Episodes should be non-overlapping and chronologically ordered
    for i in range(len(episodes) - 1):
        current_end = datetime.fromisoformat(episodes[i]["end_time"].isoformat())
        next_start = datetime.fromisoformat(episodes[i + 1]["start_time"].isoformat())
        assert current_end <= next_start, "Episodes should not overlap"
    
    # Property: Each episode should have valid structure
    for episode in episodes:
        required_episode_fields = ["start_time", "end_time", "max_tilt", "tilt_angles", "severity_score", "duration_seconds", "mean_tilt"]
        for field in required_episode_fields:
            assert field in episode, f"Missing episode field: {field}"
        
        # Property: Episode duration should be positive
        assert episode["duration_seconds"] >= 0
        
        # Property: Max tilt should be >= mean tilt
        assert episode["max_tilt"] >= episode["mean_tilt"]
        
        # Property: Tilt angles should not be empty
        assert len(episode["tilt_angles"]) > 0
        
        # Property: Mean tilt should be calculated correctly
        expected_mean = sum(episode["tilt_angles"]) / len(episode["tilt_angles"])
        assert abs(episode["mean_tilt"] - expected_mean) < 0.001
        
        # Property: Max tilt should be the maximum of tilt angles
        expected_max = max(episode["tilt_angles"])
        assert abs(episode["max_tilt"] - expected_max) < 0.001
        
        # Property: Severity score should be within valid range
        assert 0 <= episode["severity_score"] <= 3


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    readings=st.lists(sensor_reading_strategy(), min_size=10, max_size=30)
)
@settings(max_examples=30, deadline=2000)
def test_resistance_index_calculation_property(thresholds, calibration, readings):
    """
    Property: For any set of sensor readings with correction attempts, resistance index 
    calculation should be mathematically correct and within valid bounds.
    
    **Validates: Requirements 14.4, 14.7**
    """
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Filter readings to only those with correction attempts
    correction_readings = [r for r in readings if r.get("correction_attempt", False) and 
                          r.get("initial_angle") is not None and r.get("final_angle") is not None]
    
    if not correction_readings:
        # If no correction attempts, resistance index should be 0
        resistance_index = algorithm._calculate_daily_resistance_index(readings)
        assert resistance_index == 0.0
        return
    
    # Calculate resistance index
    resistance_index = algorithm._calculate_daily_resistance_index(readings)
    
    # Property: Resistance index should be non-negative (can exceed 1.0 if corrections worsen tilt)
    assert resistance_index >= 0.0
    
    # Verify manual calculation
    resistance_scores = []
    for attempt in correction_readings:
        initial_angle = attempt["initial_angle"]
        final_angle = attempt["final_angle"]
        expected_improvement = EXPECTED_CORRECTION_IMPROVEMENT
        
        actual_improvement = abs(initial_angle) - abs(final_angle)
        resistance_ratio = max(0, (expected_improvement - actual_improvement) / expected_improvement)
        resistance_scores.append(resistance_ratio)
    
    expected_resistance_index = sum(resistance_scores) / len(resistance_scores) if resistance_scores else 0.0
    assert abs(resistance_index - expected_resistance_index) < 0.001
    
    # Property: If all corrections show perfect improvement (5° or more), resistance should be 0
    perfect_corrections = all(
        (abs(r["initial_angle"]) - abs(r["final_angle"])) >= EXPECTED_CORRECTION_IMPROVEMENT 
        for r in correction_readings
    )
    if perfect_corrections:
        assert resistance_index == 0.0
    
    # Property: If corrections make angles worse, resistance index can exceed 1.0
    worsening_corrections = any(
        (abs(r["initial_angle"]) - abs(r["final_angle"])) < 0 
        for r in correction_readings
    )
    if worsening_corrections:
        assert resistance_index >= 0.0  # Can be > 1.0 in this case


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    readings=st.lists(sensor_reading_strategy(), min_size=20, max_size=100)
)
@settings(max_examples=25, deadline=3000)
def test_time_within_normal_calculation_property(thresholds, calibration, readings):
    """
    Property: For any set of sensor readings, time spent within ±5° of vertical 
    should be calculated correctly as a percentage.
    
    **Validates: Requirements 14.4**
    """
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Calculate time within normal using algorithm
    time_within_normal = algorithm._calculate_time_within_normal(readings)
    
    # Property: Time within normal should be a percentage (0-100)
    assert 0.0 <= time_within_normal <= 100.0
    
    # Verify manual calculation
    normal_readings = sum(1 for r in readings if abs(r["imu_pitch"]) <= NORMAL_THRESHOLD)
    expected_percentage = (normal_readings / len(readings)) * 100.0 if readings else 0.0
    
    assert abs(time_within_normal - expected_percentage) < 0.001
    
    # Property: If all readings are within normal range, percentage should be 100
    all_normal = all(abs(r["imu_pitch"]) <= NORMAL_THRESHOLD for r in readings)
    if all_normal:
        assert time_within_normal == 100.0
    
    # Property: If no readings are within normal range, percentage should be 0
    none_normal = all(abs(r["imu_pitch"]) > NORMAL_THRESHOLD for r in readings)
    if none_normal:
        assert time_within_normal == 0.0


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    trend_values=st.lists(st.floats(min_value=0.0, max_value=100.0, allow_nan=False), min_size=3, max_size=10)
)
@settings(max_examples=40, deadline=1000)
def test_trend_calculation_property(thresholds, calibration, trend_values):
    """
    Property: For any sequence of values, trend calculation should correctly identify 
    improving, worsening, or stable patterns.
    
    **Validates: Requirements 14.5**
    """
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Test normal trend calculation (lower values are better)
    trend_slope = algorithm._calculate_trend(trend_values, invert=True)
    
    # Property: Trend slope should be a finite number
    assert math.isfinite(trend_slope)
    
    # Test with clearly improving trend (decreasing values)
    improving_values = [10.0, 8.0, 6.0, 4.0, 2.0]
    improving_trend = algorithm._calculate_trend(improving_values, invert=True)
    assert improving_trend > 0.1, "Clearly improving trend should have positive slope when inverted"
    
    # Test with clearly worsening trend (increasing values)
    worsening_values = [2.0, 4.0, 6.0, 8.0, 10.0]
    worsening_trend = algorithm._calculate_trend(worsening_values, invert=True)
    assert worsening_trend < -0.1, "Clearly worsening trend should have negative slope when inverted"
    
    # Test with stable trend (constant values)
    stable_values = [5.0, 5.0, 5.0, 5.0, 5.0]
    stable_trend = algorithm._calculate_trend(stable_values, invert=True)
    assert abs(stable_trend) <= 0.1, "Stable trend should have slope near zero"


# Integration test combining multiple analytics properties
@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    weekly_data=weekly_sensor_readings_strategy()
)
@settings(max_examples=15, deadline=8000)
def test_comprehensive_analytics_integration_property(thresholds, calibration, weekly_data):
    """
    Property: For any weekly patient data, all analytics calculations should be 
    consistent and mathematically coherent across daily and weekly reports.
    
    **Validates: Requirements 14.4, 14.5, 14.7**
    """
    weekly_readings, end_date = weekly_data
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Generate weekly report
    weekly_report = algorithm.get_weekly_progress_report(end_date, weekly_readings)
    
    # Generate individual daily reports
    week_start = end_date - timedelta(days=6)
    daily_reports = []
    
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_readings = [
            r for r in weekly_readings 
            if datetime.fromisoformat(r["timestamp"]).date() == day.date()
        ]
        daily_report = algorithm.get_daily_metrics(day, day_readings)
        daily_reports.append(daily_report)
    
    # Property: Weekly total episodes should equal sum of daily episodes
    weekly_total_episodes = weekly_report["weekly_summary"]["total_episodes"]
    daily_total_episodes = sum(d["total_episodes"] for d in daily_reports)
    assert weekly_total_episodes == daily_total_episodes
    
    # Property: Weekly average daily episodes should be consistent
    expected_avg_daily = daily_total_episodes / 7.0
    actual_avg_daily = weekly_report["weekly_summary"]["average_daily_episodes"]
    assert abs(actual_avg_daily - expected_avg_daily) < 0.1
    
    # Property: Weekly average time within normal should be consistent
    daily_time_within_normal = [d["time_within_normal"] for d in daily_reports]
    expected_avg_time_normal = sum(daily_time_within_normal) / 7.0
    actual_avg_time_normal = weekly_report["weekly_summary"]["average_time_within_normal"]
    assert abs(actual_avg_time_normal - expected_avg_time_normal) < 0.1
    
    # Property: Daily breakdown in weekly report should match individual daily reports
    weekly_daily_breakdown = weekly_report["daily_breakdown"]
    assert len(weekly_daily_breakdown) == len(daily_reports)
    
    for i, (weekly_day, daily_report) in enumerate(zip(weekly_daily_breakdown, daily_reports)):
        assert weekly_day["date"] == daily_report["date"]
        assert weekly_day["total_episodes"] == daily_report["total_episodes"]
        assert abs(weekly_day["time_within_normal"] - daily_report["time_within_normal"]) < 0.1
    
    # Property: Peak tilt angle should be maximum of all daily max tilts
    daily_max_tilts = [d["max_tilt_angle"] for d in daily_reports if d["max_tilt_angle"] > 0]
    if daily_max_tilts:
        expected_peak_tilt = max(daily_max_tilts)
        actual_peak_tilt = weekly_report["weekly_summary"]["peak_tilt_angle"]
        assert abs(actual_peak_tilt - expected_peak_tilt) < 0.1
    
    # Property: Clinical assessment should be consistent with trend data
    trends = weekly_report["trend_analysis"]
    assessment = weekly_report["clinical_assessment"]
    
    # If episode frequency is improving, it should be mentioned in key improvements
    if trends["episode_frequency_trend"]["direction"] == "improving":
        improvements = " ".join(assessment["key_improvements"]).lower()
        assert any(word in improvements for word in ["episode", "frequency", "fewer"])
    
    # Property: Recommendations should be provided
    assert len(assessment["recommendations"]) > 0
    assert all(isinstance(rec, str) and len(rec) > 0 for rec in assessment["recommendations"])


if __name__ == "__main__":
    print("🧪 Running Clinical Analytics Calculation Property Tests...")
    print("**Validates: Requirements 14.4, 14.5, 14.7**")
    print()
    
    # Run individual property tests
    test_functions = [
        ("Daily Metrics Calculation", test_daily_metrics_calculation_property),
        ("Weekly Progress Report", test_weekly_progress_report_property),
        ("Episode Calculation Consistency", test_episode_calculation_consistency_property),
        ("Resistance Index Calculation", test_resistance_index_calculation_property),
        ("Time Within Normal Calculation", test_time_within_normal_calculation_property),
        ("Trend Calculation", test_trend_calculation_property),
        ("Comprehensive Analytics Integration", test_comprehensive_analytics_integration_property),
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
    
    print(f"\n📊 Results: {passed_tests}/{total_tests} property tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All clinical analytics calculation properties validated!")
    else:
        print("⚠️  Some property tests failed. Check clinical analytics implementation.")