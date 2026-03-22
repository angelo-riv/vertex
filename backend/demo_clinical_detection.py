#!/usr/bin/env python3
"""
Demonstration of clinical pusher syndrome detection with realistic sensor data patterns.
This shows how the algorithm detects sustained pusher episodes over time.
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta
from typing import List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinical_algorithm import (
    PusherDetectionAlgorithm, ClinicalThresholds, CalibrationData, 
    SensorDataPoint, PareticSide, SeverityScore, TiltClassification,
    create_default_thresholds, create_default_calibration
)

def simulate_pusher_episode():
    """Simulate a realistic pusher syndrome episode with sustained readings"""
    print("Clinical Pusher Syndrome Detection - Realistic Episode Simulation")
    print("=" * 70)
    
    # Setup patient and algorithm
    patient_id = "stroke_patient_001"
    device_id = "ESP32_CLINICAL_001"
    
    thresholds = create_default_thresholds(patient_id, PareticSide.RIGHT)
    calibration = create_default_calibration(patient_id, device_id)
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    print(f"Patient: {patient_id} (Right-side paretic)")
    print(f"Device: {device_id}")
    print(f"Thresholds: Normal <{thresholds.normal_threshold}°, "
          f"Pusher ≥{thresholds.pusher_threshold}°, "
          f"Severe ≥{thresholds.severe_threshold}°")
    print()
    
    # Simulate realistic sensor data sequence
    # This represents a 30-second monitoring session with a pusher episode
    sensor_sequence = [
        # Normal posture (first 5 readings)
        {"time": 0, "pitch": 2.1, "fsr_left": 2000, "fsr_right": 2100, "description": "Normal upright"},
        {"time": 1, "pitch": 1.8, "fsr_left": 2050, "fsr_right": 2000, "description": "Normal upright"},
        {"time": 2, "pitch": 2.5, "fsr_left": 1980, "fsr_right": 2120, "description": "Normal upright"},
        {"time": 3, "pitch": 1.2, "fsr_left": 2020, "fsr_right": 2080, "description": "Normal upright"},
        {"time": 4, "pitch": 3.1, "fsr_left": 1990, "fsr_right": 2110, "description": "Normal upright"},
        
        # Gradual onset of pusher episode (next 5 readings)
        {"time": 5, "pitch": 6.2, "fsr_left": 1800, "fsr_right": 2300, "description": "Mild lean onset"},
        {"time": 6, "pitch": 8.5, "fsr_left": 1650, "fsr_right": 2450, "description": "Increasing lean"},
        {"time": 7, "pitch": 11.2, "fsr_left": 1500, "fsr_right": 2600, "description": "Pusher threshold reached"},
        {"time": 8, "pitch": 13.8, "fsr_left": 1350, "fsr_right": 2750, "description": "Moderate pusher episode"},
        {"time": 9, "pitch": 15.1, "fsr_left": 1200, "fsr_right": 2900, "description": "Sustained pusher"},
        
        # Sustained pusher episode (next 8 readings - this should trigger detection)
        {"time": 10, "pitch": 16.2, "fsr_left": 1100, "fsr_right": 3000, "description": "Sustained pusher"},
        {"time": 11, "pitch": 14.8, "fsr_left": 1250, "fsr_right": 2850, "description": "Sustained pusher"},
        {"time": 12, "pitch": 17.1, "fsr_left": 1050, "fsr_right": 3050, "description": "Sustained pusher"},
        {"time": 13, "pitch": 15.9, "fsr_left": 1180, "fsr_right": 2920, "description": "Sustained pusher"},
        {"time": 14, "pitch": 16.8, "fsr_left": 1120, "fsr_right": 2980, "description": "Sustained pusher"},
        {"time": 15, "pitch": 14.2, "fsr_left": 1300, "fsr_right": 2800, "description": "Sustained pusher"},
        {"time": 16, "pitch": 18.5, "fsr_left": 950, "fsr_right": 3150, "description": "Peak pusher episode"},
        {"time": 17, "pitch": 16.7, "fsr_left": 1150, "fsr_right": 2950, "description": "Sustained pusher"},
        
        # Correction attempt (therapist intervention)
        {"time": 18, "pitch": 14.1, "fsr_left": 1400, "fsr_right": 2700, "description": "Correction attempt"},
        {"time": 19, "pitch": 16.3, "fsr_left": 1100, "fsr_right": 3000, "description": "Resistance to correction"},
        {"time": 20, "pitch": 15.8, "fsr_left": 1200, "fsr_right": 2900, "description": "Continued resistance"},
        
        # Severe episode
        {"time": 21, "pitch": 22.1, "fsr_left": 800, "fsr_right": 3300, "description": "Severe pusher episode"},
        {"time": 22, "pitch": 24.5, "fsr_left": 700, "fsr_right": 3400, "description": "Severe pusher episode"},
        {"time": 23, "pitch": 21.8, "fsr_left": 850, "fsr_right": 3250, "description": "Severe pusher episode"},
        
        # Gradual recovery
        {"time": 24, "pitch": 18.2, "fsr_left": 1000, "fsr_right": 3100, "description": "Recovery beginning"},
        {"time": 25, "pitch": 14.5, "fsr_left": 1300, "fsr_right": 2800, "description": "Improving"},
        {"time": 26, "pitch": 11.1, "fsr_left": 1500, "fsr_right": 2600, "description": "Improving"},
        {"time": 27, "pitch": 7.8, "fsr_left": 1700, "fsr_right": 2400, "description": "Near normal"},
        {"time": 28, "pitch": 4.2, "fsr_left": 1900, "fsr_right": 2200, "description": "Normal range"},
        {"time": 29, "pitch": 2.1, "fsr_left": 2000, "fsr_right": 2100, "description": "Normal upright"},
    ]
    
    print("Time | Pitch | FSR_L | FSR_R | Pusher | Severity | Classification | Description")
    print("-" * 85)
    
    base_time = datetime.now(timezone.utc)
    episode_detected = False
    max_severity = SeverityScore.NO_PUSHING
    
    for reading in sensor_sequence:
        # Create sensor data point with realistic timestamp
        timestamp = base_time + timedelta(seconds=reading["time"])
        sensor_data = SensorDataPoint(
            timestamp=timestamp,
            pitch=reading["pitch"],
            fsr_left=reading["fsr_left"],
            fsr_right=reading["fsr_right"],
            device_id=device_id
        )
        
        # Simulate correction attempt at time 18
        if reading["time"] == 18:
            algorithm.add_correction_attempt(reading["pitch"])
        elif reading["time"] == 21:
            algorithm.complete_correction_attempt(reading["pitch"])
        
        # Analyze sensor data
        analysis = algorithm.analyze_sensor_data(sensor_data)
        
        # Track episode detection
        if analysis.pusher_detected and not episode_detected:
            episode_detected = True
            print(f">>> PUSHER SYNDROME EPISODE DETECTED AT TIME {reading['time']}s <<<")
        
        if analysis.severity_score.value > max_severity.value:
            max_severity = analysis.severity_score
        
        # Display results
        print(f"{reading['time']:4d} | {reading['pitch']:5.1f} | {reading['fsr_left']:5d} | {reading['fsr_right']:5d} | "
              f"{'YES' if analysis.pusher_detected else 'NO':6s} | {analysis.severity_score.name:8s} | "
              f"{analysis.tilt_classification.value:12s} | {reading['description']}")
        
        # Highlight significant events
        if analysis.severity_score == SeverityScore.SEVERE:
            print("    ⚠️  SEVERE PUSHER EPISODE - IMMEDIATE INTERVENTION REQUIRED")
        elif analysis.pusher_detected:
            print("    ⚡ Active pusher syndrome detected")
        elif analysis.tilt_classification == TiltClassification.POTENTIAL_PUSHER:
            print("    ⚠️  Potential pusher-relevant lean detected")
    
    print("-" * 85)
    print(f"Episode Summary:")
    print(f"  - Episode detected: {'YES' if episode_detected else 'NO'}")
    print(f"  - Maximum severity: {max_severity.name}")
    print(f"  - Total readings: {len(sensor_sequence)}")
    print(f"  - Duration: {sensor_sequence[-1]['time']} seconds")
    
    # Get current episode if active
    current_episode = algorithm.get_current_episode()
    if current_episode:
        print(f"  - Active episode: {current_episode.severity_score.name}")
        print(f"  - Max tilt in episode: {current_episode.max_tilt_angle:.1f}°")
        print(f"  - Resistance index: {current_episode.resistance_index:.3f}")
    
    print(f"\n✓ Clinical detection simulation completed")
    return True

def demonstrate_different_paretic_sides():
    """Demonstrate how the algorithm handles different paretic sides"""
    print(f"\nDemonstrating Different Paretic Sides:")
    print("=" * 45)
    
    # Test data: same physical lean, different paretic sides
    test_pitch = 12.0  # Right lean
    test_fsr_left = 1500
    test_fsr_right = 2600
    
    for paretic_side in [PareticSide.LEFT, PareticSide.RIGHT]:
        print(f"\nParetic Side: {paretic_side.value.upper()}")
        print("-" * 25)
        
        thresholds = create_default_thresholds("test_patient", paretic_side)
        calibration = create_default_calibration("test_patient", "test_device")
        algorithm = PusherDetectionAlgorithm(thresholds, calibration)
        
        # Add multiple readings to build up duration
        for i in range(5):
            sensor_data = SensorDataPoint(
                timestamp=datetime.now(timezone.utc) + timedelta(seconds=i),
                pitch=test_pitch,
                fsr_left=test_fsr_left,
                fsr_right=test_fsr_right,
                device_id="test_device"
            )
            analysis = algorithm.analyze_sensor_data(sensor_data)
        
        print(f"Physical lean: {test_pitch}° to the RIGHT")
        print(f"Paretic tilt: {analysis.paretic_tilt:.1f}° ({'toward' if analysis.paretic_tilt > 0 else 'away from'} paretic side)")
        print(f"Clinical significance: {analysis.tilt_classification.value}")
        print(f"Pusher detected: {analysis.pusher_detected}")
        print(f"Severity: {analysis.severity_score.name}")

if __name__ == "__main__":
    try:
        # Run realistic episode simulation
        simulate_pusher_episode()
        
        # Demonstrate paretic side handling
        demonstrate_different_paretic_sides()
        
        print(f"\n🎉 Clinical detection demonstration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)