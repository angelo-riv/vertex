#!/usr/bin/env python3
"""
Test script for demo mode endpoints
"""

import requests
import json
import time

def test_demo_endpoints():
    base_url = "http://localhost:8000"
    
    print("=== Testing Demo Mode Endpoints ===")
    
    # Test 1: Get demo status (should be inactive initially)
    print("\n1. Testing demo status endpoint:")
    try:
        response = requests.get(f"{base_url}/api/demo/status")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Get available scenarios
    print("\n2. Testing available scenarios endpoint:")
    try:
        response = requests.get(f"{base_url}/api/demo/scenarios")
        print(f"Status Code: {response.status_code}")
        scenarios = response.json()
        print(f"Available scenarios: {len(scenarios['scenarios'])}")
        for scenario in scenarios['scenarios']:
            print(f"  - {scenario['name']}: {scenario['description']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Toggle demo mode ON
    print("\n3. Testing demo mode toggle (ON):")
    try:
        response = requests.post(f"{base_url}/api/demo/toggle?enabled=true&device_id=ESP32_TEST_001")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Wait a moment for demo to start
    time.sleep(2)
    
    # Test 4: Check demo status while active
    print("\n4. Testing demo status while active:")
    try:
        response = requests.get(f"{base_url}/api/demo/status")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Generate single demo sample
    print("\n5. Testing demo data generation:")
    try:
        response = requests.post(f"{base_url}/api/demo/generate")
        print(f"Status Code: {response.status_code}")
        sample = response.json()
        print(f"Generated sample: pitch={sample['sensor_data']['pitch']}°, pusher={sample['clinical_analysis']['pusher_detected']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 6: Set specific scenario
    print("\n6. Testing scenario change:")
    try:
        response = requests.post(f"{base_url}/api/demo/scenario/severe_pusher_episode")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 7: Toggle demo mode OFF
    print("\n7. Testing demo mode toggle (OFF):")
    try:
        response = requests.post(f"{base_url}/api/demo/toggle?enabled=false")
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Demo Mode Testing Complete ===")

if __name__ == "__main__":
    test_demo_endpoints()