"""
Test script for daily metrics calculation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone, timedelta
from clinical_algorithm import (
    PusherDetectionAlgorithm, 
    ClinicalThresholds, 
    CalibrationData,
    PareticSide
)

def test_daily_metrics_calculation():
    """Test the daily metrics calculation functionality"""
    print("Testing Daily Metrics Calculation")
    
    # Create test thresholds and calibration
    thresholds = ClinicalThresholds(
        patient_id="test_patient",
        paretic_side=PareticSide.RIGHT,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        resistance_threshold=2.0,
        episode_duration_min=2.0
    )
    
    calibration = CalibrationData(
        patient_id="test_patient",
        device_id="test_device",
        baseline_pitch=0.0,
        baseline_fsr_left=500.0,
        baseline_fsr_right=500.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=2.0,
        fsr_std_dev=50.0,
        calibration_timestamp=datetime.now(timezone.utc),
        is_active=True
    )
    
    # Create algorithm instance
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Create test sensor readings for a day
    test_date = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    test_readings = []
    
    # Generate test data with some pusher episodes
    base_time = test_date.replace(hour=9, minute=0)  # Start at 9 AM
    
    for i in range(100):  # 100 readings over the day
        timestamp = base_time + timedelta(minutes=i * 5)  # Every 5 minutes
        
        # Create some pusher episodes
        if 20 <= i <= 25 or 60 <= i <= 65:  # Two episodes during the day
            pusher_detected = True
            tilt_angle = 15.0 + (i % 3) * 2  # Varying tilt angles
            clinical_score = 2
        else:
            pusher_detected = False
            tilt_angle = 2.0 + (i % 5)  # Normal small variations
            clinical_score = 0
        
        reading = {
            'timestamp': timestamp.isoformat(),
            'imu_pitch': tilt_angle,
            'pusher_detected': pusher_detected,
            'clinical_score': clinical_score,
            'correction_attempt': pusher_detected and i % 3 == 0,  # Some correction attempts
            'initial_angle': tilt_angle,
            'final_angle': tilt_angle - 3.0 if pusher_detected else tilt_angle
        }
        test_readings.append(reading)
    
    # Calculate daily metrics
    daily_metrics = algorithm.get_daily_metrics(test_date, test_readings)
    
    print(f"\nDaily Metrics for {daily_metrics['date']}:")
    print(f"  Total Episodes: {daily_metrics['total_episodes']}")
    print(f"  Mean Tilt Angle: {daily_metrics['mean_tilt_angle']}°")
    print(f"  Max Tilt Angle: {daily_metrics['max_tilt_angle']}°")
    print(f"  Time Within Normal: {daily_metrics['time_within_normal']}%")
    print(f"  Resistance Index: {daily_metrics['resistance_index']}")
    print(f"  Correction Attempts: {daily_metrics['correction_attempts']}")
    
    # Verify results
    assert daily_metrics['total_episodes'] > 0, "Should detect episodes"
    assert daily_metrics['mean_tilt_angle'] > 0, "Should have mean tilt angle"
    assert daily_metrics['max_tilt_angle'] >= daily_metrics['mean_tilt_angle'], "Max should be >= mean"
    assert 0 <= daily_metrics['time_within_normal'] <= 100, "Time within normal should be percentage"
    assert daily_metrics['resistance_index'] >= 0, "Resistance index should be non-negative"
    
    print("✓ Daily metrics calculation test passed!")
    return True

def test_weekly_progress_report():
    """Test the weekly progress report functionality"""
    print("\nTesting Weekly Progress Report")
    
    # Create test thresholds and calibration
    thresholds = ClinicalThresholds(
        patient_id="test_patient",
        paretic_side=PareticSide.RIGHT,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        resistance_threshold=2.0,
        episode_duration_min=2.0
    )
    
    calibration = CalibrationData(
        patient_id="test_patient",
        device_id="test_device",
        baseline_pitch=0.0,
        baseline_fsr_left=500.0,
        baseline_fsr_right=500.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=2.0,
        fsr_std_dev=50.0,
        calibration_timestamp=datetime.now(timezone.utc),
        is_active=True
    )
    
    # Create algorithm instance
    algorithm = PusherDetectionAlgorithm(thresholds, calibration)
    
    # Create test sensor readings for a week with improving trend
    end_date = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    test_readings = []
    
    for day in range(7):  # 7 days
        day_date = end_date - timedelta(days=6-day)  # Start from 6 days ago
        
        # Simulate improvement over the week (fewer episodes, smaller angles)
        episode_frequency = max(1, 5 - day)  # Decreasing episodes
        max_angle = max(10, 20 - day * 2)  # Decreasing angles
        
        for hour in range(8, 18):  # 8 AM to 6 PM
            for minute in [0, 30]:  # Every 30 minutes
                timestamp = day_date.replace(hour=hour, minute=minute)
                
                # Create episodes based on frequency
                if hour % episode_frequency == 0 and minute == 0:
                    pusher_detected = True
                    tilt_angle = max_angle - (hour % 3) * 2
                    clinical_score = 2 if tilt_angle > 15 else 1
                else:
                    pusher_detected = False
                    tilt_angle = 3.0 + (hour % 3)
                    clinical_score = 0
                
                reading = {
                    'timestamp': timestamp.isoformat(),
                    'imu_pitch': tilt_angle,
                    'pusher_detected': pusher_detected,
                    'clinical_score': clinical_score,
                    'correction_attempt': pusher_detected and hour % 2 == 0,
                    'initial_angle': tilt_angle,
                    'final_angle': tilt_angle - 4.0 if pusher_detected else tilt_angle
                }
                test_readings.append(reading)
    
    # Generate weekly progress report
    weekly_report = algorithm.get_weekly_progress_report(end_date, test_readings)
    
    print(f"\nWeekly Progress Report:")
    print(f"  Period: {weekly_report['report_period']['start_date']} to {weekly_report['report_period']['end_date']}")
    print(f"  Total Episodes: {weekly_report['weekly_summary']['total_episodes']}")
    print(f"  Average Daily Episodes: {weekly_report['weekly_summary']['average_daily_episodes']}")
    print(f"  Average Mean Tilt: {weekly_report['weekly_summary']['average_mean_tilt']}°")
    print(f"  Peak Tilt Angle: {weekly_report['weekly_summary']['peak_tilt_angle']}°")
    print(f"  No Pushing Percentage: {weekly_report['weekly_summary']['no_pushing_percentage']}%")
    
    print(f"\nTrend Analysis:")
    print(f"  Episode Frequency: {weekly_report['trend_analysis']['episode_frequency_trend']['direction']}")
    print(f"  Tilt Improvement: {weekly_report['trend_analysis']['tilt_angle_improvement']['direction']}")
    print(f"  Resistance Reduction: {weekly_report['trend_analysis']['resistance_reduction']['direction']}")
    print(f"  Normal Posture Time: {weekly_report['trend_analysis']['normal_posture_time']['direction']}")
    
    print(f"\nClinical Assessment:")
    print(f"  Overall Progress: {weekly_report['clinical_assessment']['overall_progress']}")
    print(f"  Key Improvements: {weekly_report['clinical_assessment']['key_improvements']}")
    print(f"  Recommendations: {len(weekly_report['clinical_assessment']['recommendations'])} items")
    
    # Verify results
    assert weekly_report['report_period']['days_analyzed'] == 7, "Should analyze 7 days"
    assert weekly_report['weekly_summary']['total_episodes'] > 0, "Should have episodes"
    assert len(weekly_report['daily_breakdown']) == 7, "Should have 7 daily breakdowns"
    assert weekly_report['clinical_assessment']['overall_progress'] in [
        'significant_improvement', 'moderate_improvement', 'stable', 'mild_decline', 'concerning_decline'
    ], "Should have valid progress assessment"
    
    print("✓ Weekly progress report test passed!")
    return True

if __name__ == "__main__":
    print("Running Daily Metrics Tests...")
    
    try:
        test_daily_metrics_calculation()
        test_weekly_progress_report()
        print("\n✅ All daily metrics tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()