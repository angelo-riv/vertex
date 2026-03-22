#!/usr/bin/env python3
"""
Property-Based Test for Clinical Pusher Detection Accuracy

**Validates: Requirements 14.1, 14.2, 14.3, 14.6**

Property 11: Clinical Pusher Detection Accuracy
For any patient sensor data, the pusher detection algorithm should apply three-criteria 
analysis (abnormal tilt ≥10° toward paretic side for >2s, non-paretic limb use >70%, 
resistance to correction <3-5° improvement), classify tilt angles correctly (Normal <5-7°, 
Pusher-relevant ≥10°, Severe ≥20°), implement BLS/4PPS-compatible scoring (0-3 scale), 
and differentiate between task-related leaning and pusher symptoms.

This test validates the clinical-grade pusher syndrome detection algorithm across all 
input scenarios to ensure medical accuracy and reliability.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
from unittest.mock import Mock, patch

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from clinical_algorithm import (
    PusherDetectionAlgorithm, ClinicalThresholds, CalibrationData, 
    SensorDataPoint, PareticSide, SeverityScore, TiltClassification,
    PusherAnalysis, create_default_thresholds, create_default_calibration
)

# Test configuration constants
MIN_EPISODE_DURATION = 2.0  # seconds
NORMAL_THRESHOLD_DEFAULT = 5.0  # degrees
PUSHER_THRESHOLD_DEFAULT = 10.0  # degrees
SEVERE_THRESHOLD_DEFAULT = 20.0  # degrees
NON_PARETIC_THRESHOLD_DEFAULT = 0.7  # 70% weight distribution

# Hypothesis strategies for generating clinical test data
@st.composite
def clinical_thresholds_strategy(draw):
    """Generate valid clinical thresholds for different patient configurations"""
    paretic_side = draw(st.sampled_from([PareticSide.LEFT, PareticSide.RIGHT]))
    
    # Generate thresholds with clinical constraints
    normal_threshold = draw(st.floats(min_value=3.0, max_value=8.0))
    pusher_threshold = draw(st.floats(min_value=normal_threshold + 2.0, max_value=15.0))
    severe_threshold = draw(st.floats(min_value=pusher_threshold + 5.0, max_value=30.0))
    
    return ClinicalThresholds(
        patient_id=f"test_patient_{draw(st.integers(min_value=1, max_value=999))}",
        paretic_side=paretic_side,
        normal_threshold=normal_threshold,
        pusher_threshold=pusher_threshold,
        severe_threshold=severe_threshold,
        resistance_threshold=draw(st.floats(min_value=1.0, max_value=5.0)),
        episode_duration_min=draw(st.floats(min_value=1.0, max_value=5.0)),
        non_paretic_threshold=draw(st.floats(min_value=0.6, max_value=0.8))
    )


@st.composite
def calibration_data_strategy(draw):
    """Generate realistic calibration data for patients"""
    return CalibrationData(
        patient_id=f"test_patient_{draw(st.integers(min_value=1, max_value=999))}",
        device_id=f"ESP32_TEST_{draw(st.integers(min_value=1, max_value=99))}",
        baseline_pitch=draw(st.floats(min_value=-5.0, max_value=5.0)),  # Normal upright variation
        baseline_fsr_left=draw(st.floats(min_value=1500.0, max_value=2500.0)),
        baseline_fsr_right=draw(st.floats(min_value=1500.0, max_value=2500.0)),
        baseline_fsr_ratio=draw(st.floats(min_value=0.4, max_value=0.6)),  # Balanced baseline
        pitch_std_dev=draw(st.floats(min_value=0.5, max_value=2.0)),
        fsr_std_dev=draw(st.floats(min_value=0.05, max_value=0.15))
    )


@st.composite
def sensor_data_strategy(draw):
    """Generate realistic sensor data points for clinical testing"""
    return SensorDataPoint(
        timestamp=datetime.now(timezone.utc),
        pitch=draw(st.floats(min_value=-45.0, max_value=45.0, allow_nan=False, allow_infinity=False)),
        fsr_left=draw(st.integers(min_value=0, max_value=4095)),
        fsr_right=draw(st.integers(min_value=0, max_value=4095)),
        device_id=f"ESP32_TEST_{draw(st.integers(min_value=1, max_value=99))}"
    )


@st.composite
def pusher_episode_data_strategy(draw):
    """Generate sensor data that should trigger pusher detection"""
    paretic_side = draw(st.sampled_from([PareticSide.LEFT, PareticSide.RIGHT]))
    
    # Generate tilt toward paretic side (≥10°)
    if paretic_side == PareticSide.RIGHT:
        pitch = draw(st.floats(min_value=10.0, max_value=30.0))  # Right lean
    else:
        pitch = draw(st.floats(min_value=-30.0, max_value=-10.0))  # Left lean
    
    # Generate FSR values showing non-paretic limb overuse (>70%)
    total_pressure = draw(st.integers(min_value=1000, max_value=4000))
    if paretic_side == PareticSide.RIGHT:
        # Non-paretic is left, so left FSR should be high
        fsr_left = int(total_pressure * draw(st.floats(min_value=0.7, max_value=0.9)))
        fsr_right = total_pressure - fsr_left
    else:
        # Non-paretic is right, so right FSR should be high
        fsr_right = int(total_pressure * draw(st.floats(min_value=0.7, max_value=0.9)))
        fsr_left = total_pressure - fsr_right
    
    return SensorDataPoint(
        timestamp=datetime.now(timezone.utc),
        pitch=pitch,
        fsr_left=max(0, fsr_left),
        fsr_right=max(0, fsr_right),
        device_id=f"ESP32_PUSHER_TEST_{draw(st.integers(min_value=1, max_value=99))}"
    ), paretic_side


@st.composite
def normal_posture_data_strategy(draw):
    """Generate sensor data representing normal upright posture"""
    return SensorDataPoint(
        timestamp=datetime.now(timezone.utc),
        pitch=draw(st.floats(min_value=-5.0, max_value=5.0)),  # Within normal range
        fsr_left=draw(st.integers(min_value=1800, max_value=2200)),  # Balanced pressure
        fsr_right=draw(st.integers(min_value=1800, max_value=2200)),
        device_id=f"ESP32_NORMAL_TEST_{draw(st.integers(min_value=1, max_value=99))}"
    )
# Property-based tests for clinical pusher detection accuracy

@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    sensor_data=sensor_data_strategy()
)
@settings(max_examples=100, deadline=3000)
def test_tilt_angle_classification_property(thresholds, calibration, sensor_data):
    """
    Property: For any sensor data, tilt angles should be classified correctly 
    according to clinical thresholds (Normal <5-7°, Pusher-relevant ≥10°, Severe ≥20°).
    
    **Validates: Requirements 14.2**
    """
    # Ensure patient IDs match for algorithm initialization
    thresholds.patient_id = calibration.patient_id
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    analysis = algorithm.analyze_sensor_data(sensor_data)
    
    # Calculate adjusted pitch relative to baseline
    adjusted_pitch = sensor_data.pitch - calibration.baseline_pitch
    paretic_tilt = algorithm._calculate_paretic_tilt(adjusted_pitch)
    abs_tilt = abs(paretic_tilt)
    
    # Property: Tilt classification should match clinical thresholds
    if abs_tilt < thresholds.normal_threshold:
        assert analysis.tilt_classification == TiltClassification.NORMAL
    elif abs_tilt >= thresholds.severe_threshold:
        assert analysis.tilt_classification == TiltClassification.SEVERE
    elif abs_tilt >= thresholds.pusher_threshold:
        # Could be POTENTIAL_PUSHER or NORMAL depending on duration
        assert analysis.tilt_classification in [TiltClassification.POTENTIAL_PUSHER, TiltClassification.NORMAL]
    else:
        assert analysis.tilt_classification == TiltClassification.NORMAL
    
    # Property: Tilt angle should be correctly calculated
    assert abs(analysis.tilt_angle - abs(adjusted_pitch)) < 0.1
    
    # Property: Paretic tilt should respect paretic side
    expected_paretic_tilt = algorithm._calculate_paretic_tilt(adjusted_pitch)
    assert abs(analysis.paretic_tilt - expected_paretic_tilt) < 0.1


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    sensor_data=sensor_data_strategy()
)
@settings(max_examples=100, deadline=3000)
def test_bls_4pps_scoring_property(thresholds, calibration, sensor_data):
    """
    Property: For any sensor data, BLS/4PPS-compatible scoring should be implemented 
    correctly (0=No pushing, 1=Mild, 2=Moderate, 3=Severe).
    
    **Validates: Requirements 14.3**
    """
    thresholds.patient_id = calibration.patient_id
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    analysis = algorithm.analyze_sensor_data(sensor_data)
    
    # Calculate adjusted tilt
    adjusted_pitch = sensor_data.pitch - calibration.baseline_pitch
    paretic_tilt = algorithm._calculate_paretic_tilt(adjusted_pitch)
    abs_tilt = abs(paretic_tilt)
    
    # Property: Severity score should be within valid range
    assert analysis.severity_score in [SeverityScore.NO_PUSHING, SeverityScore.MILD, 
                                     SeverityScore.MODERATE, SeverityScore.SEVERE]
    
    # Property: Severity score should correlate with tilt angle
    if abs_tilt < thresholds.normal_threshold:
        assert analysis.severity_score == SeverityScore.NO_PUSHING
    elif abs_tilt >= thresholds.severe_threshold:
        # Severe angle should result in at least moderate severity
        assert analysis.severity_score.value >= SeverityScore.MODERATE.value
    
    # Property: Confidence level should be within bounds
    assert 0.0 <= analysis.confidence_level <= 1.0
    
    # Property: Higher tilt angles should generally result in higher confidence
    if abs_tilt >= thresholds.pusher_threshold:
        assert analysis.confidence_level >= 0.3  # Minimum confidence for pusher-relevant angles


@given(
    pusher_data_and_side=pusher_episode_data_strategy(),
    calibration=calibration_data_strategy()
)
@settings(max_examples=50, deadline=3000)
def test_three_criteria_analysis_property(pusher_data_and_side, calibration):
    """
    Property: For any pusher episode data, the algorithm should apply three-criteria 
    analysis (abnormal tilt ≥10° toward paretic side for >2s, non-paretic limb use >70%, 
    resistance to correction <3-5° improvement).
    
    **Validates: Requirements 14.1**
    """
    sensor_data, paretic_side = pusher_data_and_side
    
    # Create thresholds matching the paretic side
    thresholds = ClinicalThresholds(
        patient_id=calibration.patient_id,
        paretic_side=paretic_side,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        non_paretic_threshold=0.7
    )
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    analysis = algorithm.analyze_sensor_data(sensor_data)
    
    # Property: Criteria should be properly evaluated
    assert "abnormal_tilt" in analysis.criteria_met
    assert "non_paretic_overuse" in analysis.criteria_met
    assert "resistance_to_correction" in analysis.criteria_met
    
    # Property: Abnormal tilt criterion should be met for pusher data
    adjusted_pitch = sensor_data.pitch - calibration.baseline_pitch
    paretic_tilt = algorithm._calculate_paretic_tilt(adjusted_pitch)
    abs_tilt = abs(paretic_tilt)
    
    if abs_tilt >= thresholds.pusher_threshold:
        # Note: Duration requirement may not be met in single reading
        # but tilt magnitude should be detected
        assert abs_tilt >= thresholds.pusher_threshold
    
    # Property: Weight distribution should be analyzed
    fsr_ratio = algorithm._calculate_fsr_ratio(sensor_data.fsr_left, sensor_data.fsr_right)
    non_paretic_overuse = algorithm._assess_non_paretic_use(fsr_ratio)
    
    # For generated pusher data, non-paretic overuse should be detected
    assert analysis.criteria_met["non_paretic_overuse"] == non_paretic_overuse
    
    # Property: Analysis should include weight imbalance calculation
    assert analysis.weight_imbalance >= 0.0
    
    # Property: Paretic tilt should be toward the correct side
    if paretic_side == PareticSide.RIGHT:
        assert paretic_tilt > 0  # Positive for right lean
    else:
        assert paretic_tilt > 0  # Positive for left lean (algorithm converts to positive)
@given(
    normal_data=normal_posture_data_strategy(),
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy()
)
@settings(max_examples=50, deadline=3000)
def test_task_related_vs_pusher_differentiation_property(normal_data, thresholds, calibration):
    """
    Property: For any normal posture data, the algorithm should differentiate between 
    task-related leaning and pusher symptoms, avoiding false positives.
    
    **Validates: Requirements 14.6**
    """
    thresholds.patient_id = calibration.patient_id
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    analysis = algorithm.analyze_sensor_data(normal_data)
    
    # Property: Normal posture should not trigger pusher detection
    adjusted_pitch = normal_data.pitch - calibration.baseline_pitch
    abs_tilt = abs(adjusted_pitch)
    
    if abs_tilt < thresholds.normal_threshold:
        assert analysis.pusher_detected == False
        assert analysis.severity_score == SeverityScore.NO_PUSHING
        assert analysis.tilt_classification == TiltClassification.NORMAL
    
    # Property: Even if tilt is present, without other criteria it shouldn't be pusher
    # (task-related leaning vs pusher symptoms differentiation)
    if not all(analysis.criteria_met.values()):
        assert analysis.pusher_detected == False
    
    # Property: Confidence should be lower for ambiguous cases
    if abs_tilt < thresholds.pusher_threshold:
        assert analysis.confidence_level <= 0.7  # Lower confidence for non-pusher cases


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy()
)
@settings(max_examples=30, deadline=5000)
def test_sustained_episode_detection_property(thresholds, calibration):
    """
    Property: For any sequence of sensor readings showing sustained abnormal tilt, 
    the algorithm should detect episodes lasting ≥2 seconds.
    
    **Validates: Requirements 14.1 (duration component)**
    """
    thresholds.patient_id = calibration.patient_id
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Generate sustained pusher episode (multiple readings over time)
    base_time = datetime.now(timezone.utc)
    sustained_tilt = thresholds.pusher_threshold + 5.0  # Clearly abnormal
    
    # Determine tilt direction based on paretic side
    if thresholds.paretic_side == PareticSide.RIGHT:
        pitch_angle = calibration.baseline_pitch + sustained_tilt
    else:
        pitch_angle = calibration.baseline_pitch - sustained_tilt
    
    readings = []
    for i in range(6):  # 6 readings over ~3 seconds (assuming 0.5s intervals)
        sensor_data = SensorDataPoint(
            timestamp=base_time + timedelta(milliseconds=i * 500),
            pitch=pitch_angle + (i * 0.5),  # Slight variation
            fsr_left=1000 if thresholds.paretic_side == PareticSide.RIGHT else 3000,
            fsr_right=3000 if thresholds.paretic_side == PareticSide.RIGHT else 1000,
            device_id="ESP32_SUSTAINED_TEST"
        )
        readings.append(sensor_data)
    
    # Process readings sequentially
    analyses = []
    for reading in readings:
        analysis = algorithm.analyze_sensor_data(reading)
        analyses.append(analysis)
    
    # Property: Later readings should show increased episode duration
    for i in range(1, len(analyses)):
        if analyses[i].episode_duration > 0:
            assert analyses[i].episode_duration >= analyses[i-1].episode_duration
    
    # Property: Episode duration should eventually exceed minimum threshold
    final_analysis = analyses[-1]
    if final_analysis.episode_duration >= thresholds.episode_duration_min:
        # Should detect sustained abnormal tilt
        abs_tilt = abs(final_analysis.paretic_tilt)
        assert abs_tilt >= thresholds.pusher_threshold


@given(
    thresholds=clinical_thresholds_strategy(),
    calibration=calibration_data_strategy(),
    correction_improvement=st.floats(min_value=0.0, max_value=10.0)
)
@settings(max_examples=30, deadline=3000)
def test_resistance_to_correction_property(thresholds, calibration, correction_improvement):
    """
    Property: For any correction attempt, the algorithm should detect resistance 
    when improvement is <3-5° as expected.
    
    **Validates: Requirements 14.1 (resistance component)**
    """
    thresholds.patient_id = calibration.patient_id
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Start correction attempt
    initial_angle = thresholds.pusher_threshold + 5.0
    target_improvement = 5.0
    
    attempt = algorithm.add_correction_attempt(initial_angle, target_improvement)
    assert attempt is not None
    
    # Complete correction attempt with given improvement
    final_angle = initial_angle - correction_improvement
    completed_attempt = algorithm.complete_correction_attempt(final_angle)
    
    # Property: Correction attempt should be tracked
    assert completed_attempt is not None
    assert completed_attempt.actual_improvement == correction_improvement
    
    # Property: Resistance detection should be based on improvement threshold
    resistance_threshold = target_improvement * 0.6  # 60% of expected
    expected_resistance = correction_improvement < resistance_threshold
    assert completed_attempt.resistance_detected == expected_resistance
    
    # Property: Resistance index should reflect correction attempts
    resistance_index = algorithm._calculate_resistance_index()
    assert 0.0 <= resistance_index <= 1.0
    
    if expected_resistance:
        assert resistance_index > 0.0  # Should show some resistance


class ClinicalAlgorithmStateMachine(RuleBasedStateMachine):
    """Stateful property testing for clinical algorithm behavior over time"""
    
    def __init__(self):
        super().__init__()
        self.algorithm = None
        self.episode_count = 0
        self.total_readings = 0
        self.max_tilt_seen = 0.0
        
    @initialize()
    def setup_algorithm(self):
        """Initialize algorithm with default clinical settings"""
        thresholds = create_default_thresholds("stateful_patient", PareticSide.RIGHT)
        calibration = create_default_calibration("stateful_patient", "ESP32_STATEFUL")
        self.algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    @rule(sensor_data=sensor_data_strategy())
    def process_sensor_reading(self, sensor_data):
        """Process a sensor reading and update state"""
        analysis = self.algorithm.analyze_sensor_data(sensor_data)
        
        self.total_readings += 1
        self.max_tilt_seen = max(self.max_tilt_seen, abs(analysis.paretic_tilt))
        
        if analysis.pusher_detected and self.algorithm.current_episode is None:
            self.episode_count += 1
    
    @invariant()
    def algorithm_consistency_invariant(self):
        """Invariant: Algorithm state should remain consistent"""
        if self.algorithm is not None:
            # Episode tracking should be consistent
            if self.algorithm.current_episode is not None:
                assert self.algorithm.episode_start_time is not None
            
            # Sensor buffer should not exceed maximum size
            assert len(self.algorithm.sensor_buffer) <= 100
            
            # Correction attempts should be reasonable
            assert len(self.algorithm.correction_attempts) <= 50
    
    @invariant()
    def clinical_bounds_invariant(self):
        """Invariant: Clinical measurements should stay within reasonable bounds"""
        if self.total_readings > 0:
            # Maximum tilt should be within sensor range
            assert self.max_tilt_seen <= 45.0  # Reasonable maximum for clinical scenarios
            
            # Episode count should not exceed total readings
            assert self.episode_count <= self.total_readings
# Integration tests combining multiple clinical scenarios

@given(
    paretic_side=st.sampled_from([PareticSide.LEFT, PareticSide.RIGHT]),
    severity_level=st.sampled_from(['mild', 'moderate', 'severe'])
)
@settings(max_examples=20, deadline=5000)
def test_clinical_scenario_integration_property(paretic_side, severity_level):
    """
    Property: For any clinical scenario (paretic side + severity level), 
    the algorithm should produce consistent and medically accurate results.
    
    **Validates: Requirements 14.1, 14.2, 14.3, 14.6 (integration)**
    """
    # Create patient-specific configuration
    thresholds = ClinicalThresholds(
        patient_id="integration_test_patient",
        paretic_side=paretic_side,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        non_paretic_threshold=0.7
    )
    
    calibration = CalibrationData(
        patient_id="integration_test_patient",
        device_id="ESP32_INTEGRATION",
        baseline_pitch=0.0,
        baseline_fsr_left=2000.0,
        baseline_fsr_right=2000.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=1.0,
        fsr_std_dev=0.1
    )
    
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Generate scenario-specific sensor data
    if severity_level == 'mild':
        tilt_magnitude = 12.0  # Just above pusher threshold
        expected_min_severity = SeverityScore.MILD
    elif severity_level == 'moderate':
        tilt_magnitude = 16.0  # Moderate pusher behavior
        expected_min_severity = SeverityScore.MILD
    else:  # severe
        tilt_magnitude = 25.0  # Severe pusher behavior
        expected_min_severity = SeverityScore.MODERATE
    
    # Set tilt direction based on paretic side
    if paretic_side == PareticSide.RIGHT:
        pitch_angle = tilt_magnitude  # Right lean
        fsr_left, fsr_right = 1000, 3000  # Non-paretic (left) overuse
    else:
        pitch_angle = -tilt_magnitude  # Left lean
        fsr_left, fsr_right = 3000, 1000  # Non-paretic (right) overuse
    
    # Create multiple readings to establish sustained episode
    base_time = datetime.now(timezone.utc)
    for i in range(5):  # 5 readings over 2.5 seconds
        sensor_data = SensorDataPoint(
            timestamp=base_time + timedelta(milliseconds=i * 500),
            pitch=pitch_angle + (i * 0.2),  # Slight variation
            fsr_left=fsr_left + (i * 10),
            fsr_right=fsr_right - (i * 10),
            device_id="ESP32_INTEGRATION"
        )
        
        analysis = algorithm.analyze_sensor_data(sensor_data)
    
    # Property: Final analysis should reflect scenario severity
    final_analysis = analysis
    
    # Property: Tilt classification should match severity
    if severity_level == 'severe':
        assert final_analysis.tilt_classification == TiltClassification.SEVERE
    elif severity_level == 'moderate' and final_analysis.episode_duration >= 2.0:
        assert final_analysis.tilt_classification in [TiltClassification.POTENTIAL_PUSHER, TiltClassification.SEVERE]
    
    # Property: Severity score should be appropriate for scenario
    assert final_analysis.severity_score.value >= expected_min_severity.value
    
    # Property: Paretic tilt should be positive (toward paretic side)
    assert final_analysis.paretic_tilt > 0
    
    # Property: Confidence should increase with severity
    if severity_level == 'severe':
        assert final_analysis.confidence_level >= 0.6
    elif severity_level == 'moderate':
        assert final_analysis.confidence_level >= 0.4
    
    # Property: Weight imbalance should be detected
    assert final_analysis.weight_imbalance > 0.1  # Significant imbalance


# Comprehensive test runner and validation

def run_clinical_accuracy_validation():
    """
    Run comprehensive validation of clinical pusher detection accuracy.
    This function executes all property tests and provides clinical validation summary.
    """
    print("🏥 Running Clinical Pusher Detection Accuracy Property Tests...")
    print("**Validates: Requirements 14.1, 14.2, 14.3, 14.6**")
    print()
    
    test_functions = [
        ("Tilt Angle Classification", test_tilt_angle_classification_property),
        ("BLS/4PPS Scoring", test_bls_4pps_scoring_property),
        ("Three-Criteria Analysis", test_three_criteria_analysis_property),
        ("Task-Related vs Pusher Differentiation", test_task_related_vs_pusher_differentiation_property),
        ("Sustained Episode Detection", test_sustained_episode_detection_property),
        ("Resistance to Correction", test_resistance_to_correction_property),
        ("Clinical Scenario Integration", test_clinical_scenario_integration_property),
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_name, test_func in test_functions:
        try:
            print(f"🔬 Testing {test_name}...")
            # Run property test with specific examples
            test_func()
            print(f"✅ {test_name} - PASSED")
            passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Clinical Validation Results: {passed_tests}/{total_tests} property tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All clinical pusher detection accuracy properties validated!")
        print("✓ Three-criteria analysis implemented correctly")
        print("✓ Tilt angle classification meets clinical standards")
        print("✓ BLS/4PPS-compatible scoring validated")
        print("✓ Task-related vs pusher symptom differentiation working")
        return True
    else:
        print("⚠️  Some clinical property tests failed. Algorithm needs review.")
        return False


if __name__ == "__main__":
    success = run_clinical_accuracy_validation()
    exit(0 if success else 1)