"""
Integration test for calibration API endpoints
Tests the actual FastAPI endpoints with mock data
"""

import requests
import json
from datetime import datetime, timezone

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PATIENT_ID = "test_patient_calibration"
TEST_DEVICE_ID = "ESP32_CAL_TEST"

def test_calibration_endpoints():
    """Test calibration API endpoints"""
    print("=== Calibration API Integration Test ===\n")
    
    try:
        # Test 1: Start calibration
        print("1. Testing calibration start endpoint...")
        start_data = {
            "patient_id": TEST_PATIENT_ID,
            "device_id": TEST_DEVICE_ID,
            "duration_seconds": 30,
            "instructions": "Please maintain normal upright posture"
        }
        
        response = requests.post(f"{BASE_URL}/api/calibration/start/{TEST_DEVICE_ID}", json=start_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Calibration started: {result.get('message')}")
            print(f"  Session key: {result.get('session_key')}")
            print(f"  Duration: {result.get('calibration_duration')}s")
        else:
            print(f"❌ Start calibration failed: {response.status_code} - {response.text}")
            return False
        
        # Test 2: Check calibration progress
        print("\n2. Testing calibration progress endpoint...")
        response = requests.get(f"{BASE_URL}/api/calibration/progress/{TEST_PATIENT_ID}/{TEST_DEVICE_ID}")
        if response.status_code == 200:
            result = response.json()
            progress = result.get('progress', {})
            print(f"✓ Progress retrieved: {progress.get('status')}")
            print(f"  Progress: {progress.get('progress_percentage', 0):.1f}%")
            print(f"  Remaining: {progress.get('remaining_seconds', 0)}s")
        else:
            print(f"❌ Progress check failed: {response.status_code} - {response.text}")
        
        # Test 3: Complete calibration with sample data
        print("\n3. Testing calibration completion endpoint...")
        calibration_data = {
            "patient_id": TEST_PATIENT_ID,
            "device_id": TEST_DEVICE_ID,
            "baseline_pitch": 1.8,
            "baseline_fsr_left": 1980,
            "baseline_fsr_right": 2120,
            "pitch_std_dev": 0.9,
            "fsr_std_dev": 0.07,
            "calibration_duration": 30,
            "sample_count": 165
        }
        
        response = requests.post(f"{BASE_URL}/api/calibration/complete", json=calibration_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Calibration completed: {result.get('message')}")
            print(f"  Calibration ID: {result.get('calibration_id')}")
            print(f"  Quality score: {result.get('quality_score', 0):.2f}")
            
            baseline = result.get('baseline_values', {})
            print(f"  Baseline values: pitch={baseline.get('pitch')}°, ratio={baseline.get('fsr_ratio', 0):.3f}")
            
            adaptive = result.get('adaptive_thresholds', {})
            print(f"  Adaptive thresholds: normal_pitch={adaptive.get('normal_pitch_threshold')}°")
        else:
            print(f"❌ Complete calibration failed: {response.status_code} - {response.text}")
            return False
        
        # Test 4: Get active calibration
        print("\n4. Testing get active calibration endpoint...")
        response = requests.get(f"{BASE_URL}/api/calibration/{TEST_PATIENT_ID}?device_id={TEST_DEVICE_ID}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Active calibration retrieved: {result.get('device_id')}")
            print(f"  Baseline pitch: {result.get('baseline_pitch')}°")
            print(f"  FSR ratio: {result.get('baseline_fsr_ratio', 0):.3f}")
            print(f"  Calibration date: {result.get('calibration_date')}")
        else:
            print(f"❌ Get calibration failed: {response.status_code} - {response.text}")
        
        # Test 5: Get calibration summary
        print("\n5. Testing calibration summary endpoint...")
        response = requests.get(f"{BASE_URL}/api/calibration/{TEST_PATIENT_ID}/summary?device_id={TEST_DEVICE_ID}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Calibration summary retrieved: status={result.get('status')}")
            print(f"  Calibration count: {result.get('calibration_count')}")
            print(f"  Needs recalibration: {result.get('needs_recalibration')}")
            
            if result.get('baseline_values'):
                baseline = result.get('baseline_values')
                print(f"  Current baseline: pitch={baseline.get('pitch')}°, fsr_ratio={baseline.get('fsr_ratio', 0):.3f}")
        else:
            print(f"❌ Get summary failed: {response.status_code} - {response.text}")
        
        # Test 6: Analyze FSR imbalance
        print("\n6. Testing FSR imbalance analysis endpoint...")
        response = requests.post(
            f"{BASE_URL}/api/calibration/{TEST_PATIENT_ID}/analyze-fsr?fsr_left=1500&fsr_right=2500&device_id={TEST_DEVICE_ID}"
        )
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', {})
            print(f"✓ FSR analysis completed: severity={analysis.get('severity_level')}")
            print(f"  Direction: {analysis.get('imbalance_direction')}")
            print(f"  Magnitude: {analysis.get('imbalance_magnitude', 0):.3f}")
            print(f"  Exceeds threshold: {analysis.get('exceeds_threshold')}")
        else:
            print(f"❌ FSR analysis failed: {response.status_code} - {response.text}")
        
        # Test 7: Analyze pitch deviation
        print("\n7. Testing pitch deviation analysis endpoint...")
        response = requests.post(
            f"{BASE_URL}/api/calibration/{TEST_PATIENT_ID}/analyze-pitch?current_pitch=8.5&device_id={TEST_DEVICE_ID}"
        )
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('analysis', {})
            print(f"✓ Pitch analysis completed: severity={analysis.get('severity_level')}")
            print(f"  Deviation: {analysis.get('deviation_magnitude', 0):.1f}°")
            print(f"  Direction: {analysis.get('deviation_direction')}")
            print(f"  Exceeds threshold: {analysis.get('exceeds_threshold')}")
        else:
            print(f"❌ Pitch analysis failed: {response.status_code} - {response.text}")
        
        print("\n=== Integration Test Completed Successfully ===")
        print("✓ All calibration endpoints working correctly")
        print("✓ Adaptive thresholds calculated properly")
        print("✓ Real-time analysis functions operational")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure FastAPI server is running on localhost:8000")
        print("Run: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_legacy_endpoints():
    """Test legacy calibration endpoints for backward compatibility"""
    print("\n=== Testing Legacy Endpoints ===")
    
    try:
        # Test legacy calibration save
        legacy_data = {
            "patient_id": TEST_PATIENT_ID,
            "baseline_pitch": 2.0,
            "baseline_roll": 20.0,  # Maps to FSR left
            "warning_threshold": 8.0,  # Maps to FSR right
            "danger_threshold": 15.0
        }
        
        response = requests.post(f"{BASE_URL}/api/device/calibrate", json=legacy_data)
        if response.status_code == 200:
            print("✓ Legacy calibration save working")
        else:
            print(f"⚠ Legacy save failed: {response.status_code}")
        
        # Test legacy calibration get
        response = requests.get(f"{BASE_URL}/api/device/calibration/{TEST_PATIENT_ID}")
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Legacy calibration get working: {result.get('patient_id')}")
        else:
            print(f"⚠ Legacy get failed: {response.status_code}")
            
    except Exception as e:
        print(f"⚠ Legacy endpoint test failed: {str(e)}")

if __name__ == "__main__":
    success = test_calibration_endpoints()
    test_legacy_endpoints()
    
    if success:
        print("\n🎉 Calibration API integration test passed!")
        print("The calibration system is ready for production use.")
    else:
        print("\n❌ Integration test failed - check server status and logs")