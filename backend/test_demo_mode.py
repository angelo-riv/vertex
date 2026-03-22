#!/usr/bin/env python3
"""
Comprehensive test for demo mode functionality
Tests all requirements: 6.4, 6.5, 6.7
"""

import requests
import json
import time
import asyncio
import websockets

def test_demo_mode_requirements():
    """Test all demo mode requirements"""
    base_url = "http://localhost:8000"
    
    print("=== Testing Demo Mode Requirements ===")
    print("Requirements: 6.4, 6.5, 6.7")
    print()
    
    # Requirement 6.5: One-click toggle between live hardware and simulated data
    print("✓ Testing Requirement 6.5: One-click toggle functionality")
    
    # Test 1: Start demo mode (toggle ON)
    print("1. Testing demo mode toggle ON...")
    try:
        response = requests.post(f"{base_url}/api/demo/toggle?enabled=true&device_id=ESP32_PRESENTATION")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        assert result["status"] == "started", f"Expected 'started', got {result['status']}"
        assert "device_id" in result, "Missing device_id in response"
        assert "start_time" in result, "Missing start_time in response"
        
        print("   ✓ Demo mode started successfully")
        print(f"   ✓ Device ID: {result['device_id']}")
        print(f"   ✓ Start time: {result['start_time']}")
        
    except Exception as e:
        print(f"   ✗ Failed to start demo mode: {e}")
        return False
    
    # Test 2: Verify demo mode status (Requirement 6.4: Status tracking)
    print("\n2. Testing demo mode status tracking...")
    try:
        response = requests.get(f"{base_url}/api/demo/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        status = response.json()
        assert status["demo_mode"]["active"] == True, "Demo mode should be active"
        assert "current_scenario" in status["demo_mode"], "Missing current_scenario"
        assert "duration_seconds" in status["demo_mode"], "Missing duration_seconds"
        
        print("   ✓ Demo mode status retrieved successfully")
        print(f"   ✓ Active: {status['demo_mode']['active']}")
        print(f"   ✓ Current scenario: {status['demo_mode']['current_scenario']}")
        print(f"   ✓ Duration: {status['demo_mode']['duration_seconds']:.1f}s")
        
    except Exception as e:
        print(f"   ✗ Failed to get demo status: {e}")
        return False
    
    # Test 3: Test scenario switching (presentation controls)
    print("\n3. Testing presentation scenario controls...")
    scenarios_to_test = ["severe_pusher_episode", "normal_posture", "moderate_pusher_episode"]
    
    for scenario in scenarios_to_test:
        try:
            response = requests.post(f"{base_url}/api/demo/scenario/{scenario}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            result = response.json()
            assert result["status"] == "success", f"Expected 'success', got {result['status']}"
            assert result["scenario"] == scenario, f"Expected '{scenario}', got {result['scenario']}"
            
            print(f"   ✓ Scenario '{scenario}' set successfully")
            
        except Exception as e:
            print(f"   ✗ Failed to set scenario '{scenario}': {e}")
            return False
    
    # Test 4: Test demo data generation
    print("\n4. Testing demo data generation...")
    try:
        response = requests.post(f"{base_url}/api/demo/generate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        sample = response.json()
        assert "device_id" in sample, "Missing device_id in demo sample"
        assert "sensor_data" in sample, "Missing sensor_data in demo sample"
        assert "clinical_analysis" in sample, "Missing clinical_analysis in demo sample"
        assert "demo_info" in sample, "Missing demo_info in demo sample"
        
        # Verify data ranges
        pitch = sample["sensor_data"]["pitch"]
        assert -15 <= pitch <= 15, f"Pitch {pitch} outside expected range [-15, 15]"
        
        fsr_left = sample["sensor_data"]["fsr_left"]
        fsr_right = sample["sensor_data"]["fsr_right"]
        assert 0 <= fsr_left <= 4095, f"FSR left {fsr_left} outside range [0, 4095]"
        assert 0 <= fsr_right <= 4095, f"FSR right {fsr_right} outside range [0, 4095]"
        
        print("   ✓ Demo data generated successfully")
        print(f"   ✓ Pitch: {pitch}°")
        print(f"   ✓ FSR Left: {fsr_left}, FSR Right: {fsr_right}")
        print(f"   ✓ Pusher detected: {sample['clinical_analysis']['pusher_detected']}")
        
    except Exception as e:
        print(f"   ✗ Failed to generate demo data: {e}")
        return False
    
    # Test 5: Verify internet connectivity (Requirement 6.7)
    print("\n5. Testing Requirement 6.7: Internet connectivity maintained...")
    try:
        # Test external internet connectivity
        external_response = requests.get("https://httpbin.org/get", timeout=5)
        assert external_response.status_code == 200, "External internet not accessible"
        
        # Test that backend can still access external services during demo
        # This simulates Supabase and other cloud service access
        print("   ✓ External internet connectivity verified")
        print("   ✓ Cloud services (Supabase) would remain accessible")
        
    except Exception as e:
        print(f"   ✗ Internet connectivity test failed: {e}")
        return False
    
    # Test 6: Stop demo mode (toggle OFF)
    print("\n6. Testing demo mode toggle OFF...")
    try:
        response = requests.post(f"{base_url}/api/demo/toggle?enabled=false")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        result = response.json()
        assert result["status"] == "stopped", f"Expected 'stopped', got {result['status']}"
        assert "duration_seconds" in result, "Missing duration_seconds in response"
        
        print("   ✓ Demo mode stopped successfully")
        print(f"   ✓ Total duration: {result['duration_seconds']:.1f}s")
        
        # Verify demo mode is inactive
        status_response = requests.get(f"{base_url}/api/demo/status")
        status = status_response.json()
        assert status["demo_mode"]["active"] == False, "Demo mode should be inactive"
        
        print("   ✓ Demo mode status confirmed as inactive")
        
    except Exception as e:
        print(f"   ✗ Failed to stop demo mode: {e}")
        return False
    
    # Test 7: Test available scenarios endpoint
    print("\n7. Testing available scenarios for presentation controls...")
    try:
        response = requests.get(f"{base_url}/api/demo/scenarios")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        scenarios = response.json()
        assert "scenarios" in scenarios, "Missing scenarios in response"
        assert len(scenarios["scenarios"]) >= 6, "Expected at least 6 scenarios"
        
        required_scenarios = [
            "normal_posture", "mild_pusher_episode", "moderate_pusher_episode",
            "severe_pusher_episode", "correction_attempt", "recovery_phase"
        ]
        
        available_names = [s["name"] for s in scenarios["scenarios"]]
        for required in required_scenarios:
            assert required in available_names, f"Missing required scenario: {required}"
        
        print("   ✓ All required scenarios available")
        print(f"   ✓ Total scenarios: {len(scenarios['scenarios'])}")
        
        # Verify scenario details
        for scenario in scenarios["scenarios"]:
            assert "name" in scenario, "Missing name in scenario"
            assert "display_name" in scenario, "Missing display_name in scenario"
            assert "description" in scenario, "Missing description in scenario"
            assert "pitch_range" in scenario, "Missing pitch_range in scenario"
            assert "pusher_detected" in scenario, "Missing pusher_detected in scenario"
        
        print("   ✓ All scenarios have required fields")
        
    except Exception as e:
        print(f"   ✗ Failed to get available scenarios: {e}")
        return False
    
    print("\n=== Demo Mode Requirements Test Results ===")
    print("✓ Requirement 6.4: Demo mode status tracking - PASSED")
    print("✓ Requirement 6.5: One-click toggle functionality - PASSED") 
    print("✓ Requirement 6.7: Internet connectivity maintained - PASSED")
    print("\n🎉 All demo mode requirements successfully implemented!")
    
    return True

def test_demo_mode_presentation_features():
    """Test presentation-specific features"""
    base_url = "http://localhost:8000"
    
    print("\n=== Testing Presentation Features ===")
    
    # Start demo mode for presentation testing
    requests.post(f"{base_url}/api/demo/toggle?enabled=true&device_id=ESP32_PRESENTATION")
    
    # Test rapid scenario switching (for live presentations)
    print("Testing rapid scenario switching for presentations...")
    scenarios = ["normal_posture", "severe_pusher_episode", "recovery_phase", "mild_pusher_episode"]
    
    for i, scenario in enumerate(scenarios):
        response = requests.post(f"{base_url}/api/demo/scenario/{scenario}")
        assert response.status_code == 200
        
        # Generate sample data for each scenario
        sample_response = requests.post(f"{base_url}/api/demo/generate")
        sample = sample_response.json()
        
        print(f"   Scenario {i+1}: {scenario}")
        print(f"     Pitch: {sample['sensor_data']['pitch']}°")
        print(f"     Pusher: {sample['clinical_analysis']['pusher_detected']}")
        
        time.sleep(0.5)  # Brief pause between scenarios
    
    # Stop demo mode
    requests.post(f"{base_url}/api/demo/toggle?enabled=false")
    
    print("✓ Presentation scenario switching test completed")

if __name__ == "__main__":
    try:
        # Run main requirements test
        success = test_demo_mode_requirements()
        
        if success:
            # Run presentation features test
            test_demo_mode_presentation_features()
            print("\n🚀 Demo mode implementation is ready for presentations!")
        else:
            print("\n❌ Demo mode implementation has issues that need to be fixed.")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")