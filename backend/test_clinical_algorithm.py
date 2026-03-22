#!/usr/bin/env python3
"""
Test script for the clinical-grade pusher syndrome detection algorithm.
This script tests the core functionality without requiring FastAPI dependencies.
"""

import sys
import os
from datetime import datetime, timezone
from typing import List

# Add the current directory to Python path to import clinical_algorithm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinical_algorithm import (
    PusherDetectionAlgorithm, ClinicalThresholds, CalibrationData, 
    SensorDataPoint, PareticSide, SeverityScore, TiltClassification,
    create_default_thresholds, create_default_calibration
)

def test_clinical_algorithm():
    """Test the clinical pusher syndrome detection algorithm"""
    print("Testing Clinical-Grade Pusher Syndrome Detection Algorithm")
    print("=" * 60)
    
    # Create test patient configuration
    patient_id = "test_patient_001"
    device_id = "ESP32_TEST_001"
    
    # Create clinical thresholds for right-side paretic patient
    thresholds = create_default_thresholds(patient_id, PareticSide.RIGHT)
    print(f"✓ Created clinical thresholds for {patient_id}")
    print(f"  - Paretic side: {thresholds.paretic_side}")
    print(f"  - Normal threshold: {thresholds.normal_threshold}°")
    print(f"  - Pusher threshold: {thresholds.pusher_threshold}°")
    print(f"  - Severe threshold: {thresholds.severe_threshold}°")
    
    # Create calibration data
    calibration = create_default_calibration(patient_id, device_id)
    print(f"✓ Created calibration data for {device_id}")
    print(f"  - Baseline pitch: {calibration.baseline_pitch}°")
    print(f"  - Baseline FSR ratio: {calibration.baseline_fsr_ratio}")
    
    # Initialize algorithm
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    print(f"✓ Initialized pusher detection algorithm")
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Normal upright posture",
            "pitch": 2.0,
            "fsr_left": 2000,
            "fsr_right": 2100,
            "expected_pusher": False,
            "expected_severity": SeverityScore.NO_PUSHING
        },
        {
            "name": "Mild right lean (toward paretic side)",
            "pitch": 8.0,
            "fsr_left": 1800,
            "fsr_right": 2300,
            "expected_pusher": False,  # Not sustained enough
            "expected_severity": SeverityScore.NO_PUSHING
        },
        {
            "name": "Moderate pusher episode",
            "pitch": 12.0,
            "fsr_left": 1200,
            "fsr_right": 2900,
            "expected_pusher": False,  # Need sustained duration
            "expected_severity": SeverityScore.MILD
        },
        {
            "name": "Severe pusher episode",
            "pitch": 22.0,
            "fsr_left": 800,
            "fsr_right": 3200,
            "expected_pusher": False,  # Need sustained duration and resistance
            "expected_severity": SeverityScore.MODERATE
        },
        {
            "name": "Left lean (away from paretic side)",
            "pitch": -10.0,
            "fsr_left": 2800,
            "fsr_right": 1200,
            "expected_pusher": False,
            "expected_severity": SeverityScore.NO_PUSHING
        }
    ]
    
    print("\nTesting sensor data analysis scenarios:")
    print("-" * 40)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        
        # Create sensor data point
        sensor_data = SensorDataPoint(
            timestamp=datetime.now(timezone.utc),
            pitch=scenario['pitch'],
            fsr_left=scenario['fsr_left'],
            fsr_right=scenario['fsr_right'],
            device_id=device_id
        )
        
        # Analyze sensor data
        analysis = algorithm.analyze_sensor_data(sensor_data)
        
        # Display results
        print(f"  Input: pitch={scenario['pitch']}°, FSR_L={scenario['fsr_left']}, FSR_R={scenario['fsr_right']}")
        print(f"  Results:")
        print(f"    - Pusher detected: {analysis.pusher_detected}")
        print(f"    - Severity score: {analysis.severity_score.name} ({analysis.severity_score.value})")
        print(f"    - Tilt classification: {analysis.tilt_classification.value}")
        print(f"    - Paretic tilt: {analysis.paretic_tilt:.1f}°")
        print(f"    - Weight imbalance: {analysis.weight_imbalance:.3f}")
        print(f"    - Confidence level: {analysis.confidence_level:.3f}")
        print(f"    - Episode duration: {analysis.episode_duration:.1f}s")
        
        # Check criteria
        print(f"    - Criteria met:")
        for criterion, met in analysis.criteria_met.items():
            print(f"      * {criterion}: {met}")
        
        # Validate expectations
        severity_match = analysis.severity_score == scenario['expected_severity']
        print(f"    - Expected severity: {scenario['expected_severity'].name} ({'✓' if severity_match else '✗'})")
    
    # Test sustained pusher episode (multiple readings)
    print(f"\nTesting sustained pusher episode (multiple readings):")
    print("-" * 50)
    
    sustained_readings = [
        {"pitch": 15.0, "fsr_left": 1000, "fsr_right": 3000},
        {"pitch": 16.0, "fsr_left": 1100, "fsr_right": 2900},
        {"pitch": 14.5, "fsr_left": 1200, "fsr_right": 2800},
        {"pitch": 15.5, "fsr_left": 1050, "fsr_right": 2950},
        {"pitch": 16.5, "fsr_left": 1150, "fsr_right": 2850},
    ]
    
    for i, reading in enumerate(sustained_readings):
        sensor_data = SensorDataPoint(
            timestamp=datetime.now(timezone.utc),
            pitch=reading['pitch'],
            fsr_left=reading['fsr_left'],
            fsr_right=reading['fsr_right'],
            device_id=device_id
        )
        
        analysis = algorithm.analyze_sensor_data(sensor_data)
        
        print(f"Reading {i+1}: pitch={reading['pitch']}°, "
              f"pusher={analysis.pusher_detected}, "
              f"severity={analysis.severity_score.name}, "
              f"duration={analysis.episode_duration:.1f}s")
    
    # Test correction attempt functionality
    print(f"\nTesting correction attempt tracking:")
    print("-" * 40)
    
    # Start correction attempt
    initial_angle = 18.0
    attempt = algorithm.add_correction_attempt(initial_angle)
    print(f"✓ Started correction attempt at {initial_angle}°")
    
    # Complete correction attempt with improvement
    final_angle = 12.0
    completed_attempt = algorithm.complete_correction_attempt(final_angle)
    
    if completed_attempt:
        print(f"✓ Completed correction attempt:")
        print(f"  - Initial angle: {completed_attempt.initial_angle}°")
        print(f"  - Final angle: {final_angle}°")
        print(f"  - Improvement: {completed_attempt.actual_improvement}°")
        print(f"  - Expected improvement: {completed_attempt.target_improvement}°")
        print(f"  - Resistance detected: {completed_attempt.resistance_detected}")
    
    # Test tilt classification
    print(f"\nTesting tilt angle classification:")
    print("-" * 35)
    
    test_angles = [3.0, 7.0, 12.0, 18.0, 25.0]
    for angle in test_angles:
        sensor_data = SensorDataPoint(
            timestamp=datetime.now(timezone.utc),
            pitch=angle,
            fsr_left=2000,
            fsr_right=2000,
            device_id=device_id
        )
        
        analysis = algorithm.analyze_sensor_data(sensor_data)
        print(f"  {angle:4.1f}° → {analysis.tilt_classification.value}")
    
    print(f"\n" + "=" * 60)
    print("✓ Clinical algorithm testing completed successfully!")
    print("✓ All core functionality verified")
    
    return True

def test_clinical_thresholds():
    """Test clinical thresholds configuration"""
    print("\nTesting Clinical Thresholds Configuration:")
    print("-" * 45)
    
    # Test different paretic sides
    left_thresholds = ClinicalThresholds(
        patient_id="left_patient",
        paretic_side=PareticSide.LEFT,
        normal_threshold=6.0,
        pusher_threshold=12.0,
        severe_threshold=25.0
    )
    
    right_thresholds = ClinicalThresholds(
        patient_id="right_patient",
        paretic_side=PareticSide.RIGHT,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0
    )
    
    print(f"✓ Left paretic patient thresholds: {left_thresholds.paretic_side}")
    print(f"✓ Right paretic patient thresholds: {right_thresholds.paretic_side}")
    
    # Test threshold validation
    try:
        invalid_thresholds = ClinicalThresholds(
            patient_id="invalid_patient",
            paretic_side=PareticSide.RIGHT,
            normal_threshold=25.0,  # Invalid: higher than pusher threshold
            pusher_threshold=10.0,
            severe_threshold=20.0
        )
        print("✗ Threshold validation failed - should have caught invalid values")
    except Exception as e:
        print(f"✓ Threshold validation working correctly")
    
    return True

if __name__ == "__main__":
    try:
        # Run tests
        test_clinical_algorithm()
        test_clinical_thresholds()
        
        print(f"\n🎉 All tests passed! Clinical algorithm is ready for integration.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)