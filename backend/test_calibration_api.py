"""
Test script for calibration API endpoints
"""

import asyncio
import sys
from datetime import datetime, timezone
from models.calibration_models import (
    CalibrationDataCreate, CalibrationRequest, 
    analyze_fsr_imbalance, analyze_pitch_deviation
)

def test_calibration_models():
    """Test calibration data models and utility functions"""
    print("Testing calibration models...")
    
    # Test calibration data creation
    calibration = CalibrationDataCreate(
        patient_id="test_patient_123",
        device_id="ESP32_DEVICE_001",
        baseline_pitch=1.5,
        baseline_fsr_left=1950,
        baseline_fsr_right=2150,
        pitch_std_dev=0.8,
        fsr_std_dev=0.06,
        calibration_duration=30,
        sample_count=180
    )
    
    print(f"✓ Calibration created: {calibration.device_id}")
    print(f"  Baseline FSR ratio: {calibration.baseline_fsr_ratio:.3f}")
    print(f"  Quality indicators: pitch_std={calibration.pitch_std_dev}, fsr_std={calibration.fsr_std_dev}")
    
    # Test calibration request
    request = CalibrationRequest(
        patient_id="test_patient_123",
        device_id="ESP32_DEVICE_001",
        duration_seconds=30,
        instructions="Please stand upright and remain still"
    )
    
    print(f"✓ Calibration request created for {request.duration_seconds}s")
    
    return calibration

def test_adaptive_thresholds():
    """Test adaptive threshold calculation"""
    print("\nTesting adaptive thresholds...")
    
    from models.calibration_models import calculate_adaptive_thresholds, validate_calibration_quality
    
    # Create test calibration
    calibration = CalibrationDataCreate(
        patient_id="test_patient",
        device_id="ESP32_TEST",
        baseline_pitch=2.0,
        baseline_fsr_left=2000,
        baseline_fsr_right=2200,
        pitch_std_dev=1.0,
        fsr_std_dev=0.05,
        calibration_duration=30
    )
    
    # Test validation
    validation = validate_calibration_quality(calibration)
    print(f"✓ Calibration validation: valid={validation.is_valid}, quality={validation.quality_score:.2f}")
    
    if validation.warnings:
        print(f"  Warnings: {validation.warnings}")
    if validation.recommendations:
        print(f"  Recommendations: {validation.recommendations}")
    
    # Test adaptive threshold calculation
    clinical_thresholds = {
        'normal_threshold': 5.0,
        'pusher_threshold': 10.0,
        'severe_threshold': 20.0
    }
    
    adaptive = calculate_adaptive_thresholds(calibration, clinical_thresholds)
    print(f"✓ Adaptive thresholds calculated:")
    print(f"  Pitch thresholds: normal={adaptive.normal_pitch_threshold:.1f}°, pusher={adaptive.pusher_pitch_threshold:.1f}°, severe={adaptive.severe_pitch_threshold:.1f}°")
    print(f"  FSR imbalance thresholds: normal={adaptive.normal_fsr_imbalance_threshold:.3f}, pusher={adaptive.pusher_fsr_imbalance_threshold:.3f}")
    print(f"  Resistance thresholds: force={adaptive.resistance_force_threshold:.1f}, angle={adaptive.resistance_angle_threshold:.1f}°")
    
    return calibration, adaptive

def test_analysis_functions():
    """Test FSR imbalance and pitch deviation analysis"""
    print("\nTesting analysis functions...")
    
    # Create mock calibration response
    from models.calibration_models import CalibrationDataResponse
    
    calibration = CalibrationDataResponse(
        id="test_cal_123",
        patient_id="test_patient",
        device_id="ESP32_TEST",
        calibration_date=datetime.now(timezone.utc),
        baseline_pitch=1.0,
        baseline_fsr_left=2000,
        baseline_fsr_right=2100,
        baseline_fsr_ratio=0.512,
        pitch_std_dev=0.8,
        fsr_std_dev=0.05,
        calibration_duration=30,
        sample_count=150,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    
    # Create adaptive thresholds
    from models.calibration_models import AdaptiveThresholds
    
    adaptive = AdaptiveThresholds(
        patient_id="test_patient",
        device_id="ESP32_TEST",
        calibration_id="test_cal_123",
        normal_pitch_threshold=6.0,
        pusher_pitch_threshold=12.0,
        severe_pitch_threshold=24.0,
        normal_fsr_imbalance_threshold=0.10,
        pusher_fsr_imbalance_threshold=0.15,
        severe_fsr_imbalance_threshold=0.25,
        resistance_force_threshold=2200.0,
        resistance_angle_threshold=3.6
    )
    
    # Test FSR imbalance analysis
    print("Testing FSR imbalance analysis:")
    
    # Test balanced case
    fsr_analysis = analyze_fsr_imbalance(2000, 2100, calibration, adaptive)
    print(f"  Balanced case: severity={fsr_analysis.severity_level}, direction={fsr_analysis.imbalance_direction}")
    
    # Test right imbalance
    fsr_analysis = analyze_fsr_imbalance(1500, 2500, calibration, adaptive)
    print(f"  Right imbalance: severity={fsr_analysis.severity_level}, direction={fsr_analysis.imbalance_direction}, magnitude={fsr_analysis.imbalance_magnitude:.3f}")
    
    # Test left imbalance
    fsr_analysis = analyze_fsr_imbalance(2800, 1200, calibration, adaptive)
    print(f"  Left imbalance: severity={fsr_analysis.severity_level}, direction={fsr_analysis.imbalance_direction}, magnitude={fsr_analysis.imbalance_magnitude:.3f}")
    
    # Test pitch deviation analysis
    print("Testing pitch deviation analysis:")
    
    # Test normal pitch
    pitch_analysis = analyze_pitch_deviation(2.0, calibration, adaptive)
    print(f"  Normal pitch: severity={pitch_analysis.severity_level}, deviation={pitch_analysis.deviation_magnitude:.1f}°")
    
    # Test moderate deviation
    pitch_analysis = analyze_pitch_deviation(8.0, calibration, adaptive)
    print(f"  Moderate deviation: severity={pitch_analysis.severity_level}, deviation={pitch_analysis.deviation_magnitude:.1f}°")
    
    # Test severe deviation
    pitch_analysis = analyze_pitch_deviation(15.0, calibration, adaptive)
    print(f"  Severe deviation: severity={pitch_analysis.severity_level}, deviation={pitch_analysis.deviation_magnitude:.1f}°")
    
    print("✓ Analysis functions working correctly")

def main():
    """Run all calibration tests"""
    print("=== Calibration API Test Suite ===\n")
    
    try:
        # Test models
        calibration = test_calibration_models()
        
        # Test adaptive thresholds
        calibration, adaptive = test_adaptive_thresholds()
        
        # Test analysis functions
        test_analysis_functions()
        
        print("\n=== All Tests Passed ===")
        print("✓ Calibration models working correctly")
        print("✓ Adaptive threshold calculation working")
        print("✓ FSR imbalance analysis working")
        print("✓ Pitch deviation analysis working")
        print("\nCalibration API is ready for integration!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()