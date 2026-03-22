"""
Test script for clinical analytics API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_daily_metrics_endpoint():
    """Test the daily metrics API endpoint"""
    print("Testing Daily Metrics Endpoint...")
    
    # Test with default date (today)
    response = requests.get(f"{BASE_URL}/api/clinical/daily-metrics/test_patient")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Verify response structure
        assert "patient_id" in data
        assert "date" in data
        assert "metrics" in data
        assert "data_points" in data
        assert "status" in data
        
        metrics = data["metrics"]
        assert "total_episodes" in metrics
        assert "mean_tilt_angle" in metrics
        assert "max_tilt_angle" in metrics
        assert "time_within_normal" in metrics
        assert "resistance_index" in metrics
        assert "correction_attempts" in metrics
        
        print("✓ Daily metrics endpoint test passed!")
    else:
        print(f"❌ Request failed: {response.text}")
    
    return response.status_code == 200

def test_weekly_report_endpoint():
    """Test the weekly progress report API endpoint"""
    print("\nTesting Weekly Progress Report Endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/clinical/weekly-report/test_patient")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Verify response structure
        assert "patient_id" in data
        assert "report" in data
        assert "data_points" in data
        assert "status" in data
        
        report = data["report"]
        assert "report_period" in report
        assert "weekly_summary" in report
        assert "trend_analysis" in report
        assert "clinical_assessment" in report
        assert "daily_breakdown" in report
        
        print("✓ Weekly progress report endpoint test passed!")
    else:
        print(f"❌ Request failed: {response.text}")
    
    return response.status_code == 200

def test_episode_frequency_endpoint():
    """Test the episode frequency tracking API endpoint"""
    print("\nTesting Episode Frequency Endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/clinical/episode-frequency/test_patient?days=7")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Verify response structure
        assert "patient_id" in data
        assert "period" in data
        assert "frequency_data" in data
        assert "episodes_detail" in data
        
        frequency_data = data["frequency_data"]
        assert "daily_counts" in frequency_data
        assert "total_episodes" in frequency_data
        assert "average_daily_episodes" in frequency_data
        assert "maximum_daily_episodes" in frequency_data
        assert "trend" in frequency_data
        
        print("✓ Episode frequency endpoint test passed!")
    else:
        print(f"❌ Request failed: {response.text}")
    
    return response.status_code == 200

def test_resistance_index_endpoint():
    """Test the resistance index analysis API endpoint"""
    print("\nTesting Resistance Index Endpoint...")
    
    response = requests.get(f"{BASE_URL}/api/clinical/resistance-index/test_patient?days=7")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        
        # Verify response structure
        assert "patient_id" in data
        assert "period" in data
        assert "resistance_analysis" in data
        assert "detailed_data" in data
        
        resistance_analysis = data["resistance_analysis"]
        assert "average_resistance_index" in resistance_analysis
        assert "correction_success_rate" in resistance_analysis
        assert "total_correction_attempts" in resistance_analysis
        assert "successful_corrections" in resistance_analysis
        
        print("✓ Resistance index endpoint test passed!")
    else:
        print(f"❌ Request failed: {response.text}")
    
    return response.status_code == 200

def test_health_check():
    """Test that the server is responding"""
    print("Testing Health Check...")
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Health Check Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Server is healthy!")
        return True
    else:
        print("❌ Server health check failed!")
        return False

if __name__ == "__main__":
    print("Testing Clinical Analytics API Endpoints...")
    
    try:
        # Test server health first
        if not test_health_check():
            print("❌ Server is not responding. Make sure the backend is running.")
            exit(1)
        
        # Test all endpoints
        results = []
        results.append(test_daily_metrics_endpoint())
        results.append(test_weekly_report_endpoint())
        results.append(test_episode_frequency_endpoint())
        results.append(test_resistance_index_endpoint())
        
        if all(results):
            print("\n✅ All clinical analytics endpoint tests passed!")
        else:
            print(f"\n❌ Some tests failed. Results: {results}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()