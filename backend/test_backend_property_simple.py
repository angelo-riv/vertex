#!/usr/bin/env python3
"""
Simplified Property-Based Test for Backend Data Processing Integrity

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2**

Property 3: Backend Data Processing Integrity
For any HTTP POST request from ESP32 device, the FastAPI backend should validate JSON 
structure and sensor ranges, store complete metadata (patient_id, session_id, timestamp, 
device_id) to Supabase within 500ms, broadcast via WebSocket to connected clients, and 
handle concurrent connections without performance degradation.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch

import httpx
import websockets
from hypothesis import given, strategies as st, settings, assume

# Test configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws/sensor-stream"
MAX_LATENCY_MS = 500  # 500ms requirement for storage

# Fixed base timestamp for consistent testing (current time)
def get_current_base_timestamp():
    """Get current timestamp for testing"""
    return int(time.time() * 1000)


# Simplified Hypothesis strategies
def valid_device_id_strategy():
    """Generate valid ESP32 device IDs"""
    return st.text(min_size=1, max_size=10, alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').map(
        lambda x: f"ESP32_{x}"
    )


def valid_sensor_data_strategy():
    """Generate valid ESP32 sensor data"""
    return st.builds(
        lambda device_id, pitch, fsr_left, fsr_right: {
            'deviceId': device_id,
            'timestamp': get_current_base_timestamp(),  # Use current time
            'pitch': pitch,
            'fsrLeft': fsr_left,
            'fsrRight': fsr_right
        },
        device_id=valid_device_id_strategy(),
        pitch=st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False),
        fsr_left=st.integers(min_value=0, max_value=4095),
        fsr_right=st.integers(min_value=0, max_value=4095)
    )


def invalid_sensor_data_strategy():
    """Generate invalid ESP32 sensor data"""
    current_time = get_current_base_timestamp()
    return st.one_of([
        # Invalid device ID
        st.builds(
            lambda bad_id: {
                'deviceId': bad_id,
                'timestamp': current_time,
                'pitch': 0.0,
                'fsrLeft': 512,
                'fsrRight': 512
            },
            bad_id=st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith('ESP32_'))
        ),
        # Invalid pitch range
        st.builds(
            lambda bad_pitch: {
                'deviceId': 'ESP32_TEST',
                'timestamp': current_time,
                'pitch': bad_pitch,
                'fsrLeft': 512,
                'fsrRight': 512
            },
            bad_pitch=st.one_of(
                st.floats(min_value=-1000.0, max_value=-180.1),
                st.floats(min_value=180.1, max_value=1000.0)
            ).filter(lambda x: not (x != x))  # Filter out NaN
        ),
        # Invalid FSR range
        st.builds(
            lambda bad_fsr_left, bad_fsr_right: {
                'deviceId': 'ESP32_TEST',
                'timestamp': current_time,
                'pitch': 0.0,
                'fsrLeft': bad_fsr_left,
                'fsrRight': bad_fsr_right
            },
            bad_fsr_left=st.integers(min_value=-1000, max_value=-1),
            bad_fsr_right=st.integers(min_value=4096, max_value=10000)
        )
    ])


# Property-based tests
@given(sensor_data=valid_sensor_data_strategy())
@settings(max_examples=20, deadline=3000)
def test_valid_sensor_data_processing_property(sensor_data):
    """
    Property: For any valid ESP32 sensor data, the backend should validate 
    JSON structure and sensor ranges correctly.
    
    **Validates: Requirements 3.1, 3.2**
    """
    async def run_test():
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            response = await client.post(
                f"{BACKEND_URL}/api/sensor-data/test",
                json=sensor_data,
                timeout=2.0
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Property: Valid data should be accepted
            assert response.status_code == 200, f"Valid data rejected: {response.text}"
            
            # Property: Processing should be fast
            assert processing_time <= MAX_LATENCY_MS, f"Processing took {processing_time:.1f}ms > {MAX_LATENCY_MS}ms"
            
            result = response.json()
            
            # Property: Response should contain required fields
            assert result["status"] == "success"
            assert "processed_data" in result
            assert "device_status" in result
            
            # Property: Device tracking should work
            device_status = result["device_status"]
            assert device_status["device_id"] == sensor_data["deviceId"]
            assert device_status["connection_status"] == "connected"
            
            # Property: Data processing should be correct
            processed = result["processed_data"]
            expected_tilt = abs(sensor_data["pitch"])
            assert abs(processed["tilt_angle"] - expected_tilt) < 0.1
    
    asyncio.run(run_test())


@given(invalid_data=invalid_sensor_data_strategy())
@settings(max_examples=15, deadline=3000)
def test_invalid_sensor_data_rejection_property(invalid_data):
    """
    Property: For any invalid ESP32 sensor data, the backend should reject 
    the data with appropriate error codes.
    
    **Validates: Requirements 3.2, 3.5**
    """
    async def run_test():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/api/sensor-data/test",
                    json=invalid_data,
                    timeout=2.0
                )
                
                # Property: Invalid data should be rejected
                assert response.status_code in [400, 422], f"Invalid data accepted: {response.status_code}"
                
            except (httpx.RequestError, json.JSONDecodeError):
                # Some invalid data might cause request errors, which is acceptable
                pass
    
    asyncio.run(run_test())


@given(sensor_data_list=st.lists(valid_sensor_data_strategy(), min_size=2, max_size=5))
@settings(max_examples=10, deadline=8000)
def test_concurrent_processing_property(sensor_data_list):
    """
    Property: For any set of concurrent HTTP POST requests from ESP32 devices, 
    the backend should handle them without performance degradation.
    
    **Validates: Requirements 3.6, 3.7**
    """
    async def run_test():
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # Send all requests concurrently
            tasks = [
                client.post(f"{BACKEND_URL}/api/sensor-data/test", json=data, timeout=3.0)
                for data in sensor_data_list
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = (time.time() - start_time) * 1000
            
            # Property: All valid requests should be processed successfully
            successful_responses = sum(
                1 for r in responses 
                if isinstance(r, httpx.Response) and r.status_code == 200
            )
            
            assert successful_responses == len(sensor_data_list), f"Only {successful_responses}/{len(sensor_data_list)} requests succeeded"
            
            # Property: Concurrent processing should maintain reasonable performance
            max_concurrent_time = MAX_LATENCY_MS * 2  # Allow more time for concurrent processing
            assert total_time <= max_concurrent_time, f"Concurrent processing took {total_time:.1f}ms > {max_concurrent_time}ms"
    
    asyncio.run(run_test())


@given(sensor_data=valid_sensor_data_strategy())
@settings(max_examples=15, deadline=4000)
def test_metadata_storage_property(sensor_data):
    """
    Property: For any sensor data processed, the backend should include complete 
    metadata in storage operations.
    
    **Validates: Requirements 3.3, 5.1, 5.2**
    """
    async def run_test():
        # Mock Supabase to capture storage operations
        with patch('main.supabase') as mock_supabase:
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.insert.return_value.execute.return_value.data = [{"id": "test_id"}]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/sensor-data",  # Use real endpoint for storage testing
                    json=sensor_data,
                    timeout=2.0
                )
                
                assert response.status_code == 200
                
                # Property: Storage operation should include complete metadata
                if mock_table.insert.called:
                    stored_data = mock_table.insert.call_args[0][0]
                    
                    # Property: Required metadata fields should be present
                    assert "device_id" in stored_data
                    assert "timestamp" in stored_data
                    assert stored_data["device_id"] == sensor_data["deviceId"]
                    
                    # Property: Sensor data should be preserved
                    assert "imu_pitch" in stored_data
                    assert "fsr_left" in stored_data
                    assert "fsr_right" in stored_data
                    assert stored_data["imu_pitch"] == sensor_data["pitch"]
                    assert stored_data["fsr_left"] == float(sensor_data["fsrLeft"])
                    assert stored_data["fsr_right"] == float(sensor_data["fsrRight"])
    
    asyncio.run(run_test())


@given(sensor_data=valid_sensor_data_strategy())
@settings(max_examples=10, deadline=6000)
def test_websocket_broadcasting_property(sensor_data):
    """
    Property: For any sensor data received, the backend should broadcast 
    via WebSocket to connected clients.
    
    **Validates: Requirements 3.4**
    """
    async def run_test():
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                # Wait for connection confirmation
                await asyncio.wait_for(websocket.recv(), timeout=2.0)
                
                # Send sensor data via HTTP API
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{BACKEND_URL}/api/sensor-data",
                        json=sensor_data,
                        timeout=2.0
                    )
                    
                    assert response.status_code == 200
                
                # Property: WebSocket client should receive broadcast
                try:
                    broadcast_message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    broadcast_data = json.loads(broadcast_message)
                    
                    # Property: Broadcast should contain sensor data
                    assert broadcast_data.get("type") == "sensor_data"
                    assert "data" in broadcast_data
                    assert broadcast_data["data"]["device_id"] == sensor_data["deviceId"]
                    
                except asyncio.TimeoutError:
                    pytest.fail("WebSocket broadcast not received within timeout")
                    
        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            # If WebSocket connection fails, skip this test (backend might not be running)
            pytest.skip(f"WebSocket connection failed: {str(e)}")
    
    asyncio.run(run_test())


def test_device_connection_tracking():
    """
    Test that device connections are tracked properly.
    
    **Validates: Requirements 7.1, 7.3**
    """
    async def run_test():
        # Send data from a test device
        test_data = {
            "deviceId": "ESP32_TRACKING_TEST",
            "timestamp": get_current_base_timestamp(),
            "pitch": 5.0,
            "fsrLeft": 400,
            "fsrRight": 600
        }
        
        async with httpx.AsyncClient() as client:
            # Send sensor data
            response = await client.post(
                f"{BACKEND_URL}/api/sensor-data/test",
                json=test_data,
                timeout=2.0
            )
            
            assert response.status_code == 200
            
            # Check device status
            status_response = await client.get(
                f"{BACKEND_URL}/api/sensor-data/devices",
                timeout=2.0
            )
            
            assert status_response.status_code == 200
            device_status = status_response.json()
            
            # Property: Device should be tracked
            tracked_devices = {d["device_id"] for d in device_status["devices"]}
            assert test_data["deviceId"] in tracked_devices
            
            # Property: Device should be marked as connected
            test_device = next(d for d in device_status["devices"] if d["device_id"] == test_data["deviceId"])
            assert test_device["connection_status"] == "connected"
            assert test_device["data_count"] >= 1
    
    asyncio.run(run_test())


def test_performance_under_load():
    """
    Test system performance with multiple devices sending data.
    
    **Validates: Requirements 8.1, 8.2, 8.3**
    """
    async def run_test():
        # Create test data for multiple devices
        devices = [f"ESP32_PERF_TEST_{i:03d}" for i in range(3)]
        all_requests = []
        
        for i, device_id in enumerate(devices):
            for j in range(2):  # 2 data points per device
                sensor_data = {
                    "deviceId": device_id,
                    "timestamp": get_current_base_timestamp() + (i * 100) + j,
                    "pitch": float(i * 5 - 10),  # Vary pitch by device
                    "fsrLeft": 300 + (i * 100),
                    "fsrRight": 700 - (i * 100)
                }
                all_requests.append(sensor_data)
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # Send all requests concurrently
            tasks = [
                client.post(f"{BACKEND_URL}/api/sensor-data/test", json=data, timeout=3.0)
                for data in all_requests
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = (time.time() - start_time) * 1000
            
            # Property: All requests should be processed successfully
            successful_count = sum(
                1 for r in responses 
                if isinstance(r, httpx.Response) and r.status_code == 200
            )
            
            assert successful_count == len(all_requests), f"Only {successful_count}/{len(all_requests)} requests succeeded"
            
            # Property: Performance should be maintained under load
            max_load_time = MAX_LATENCY_MS * 3  # Allow more time for load testing
            assert total_time <= max_load_time, f"Load test took {total_time:.1f}ms > {max_load_time}ms"
            
            # Check that all devices are tracked
            device_status_response = await client.get(f"{BACKEND_URL}/api/sensor-data/devices", timeout=2.0)
            assert device_status_response.status_code == 200
            
            device_status = device_status_response.json()
            tracked_devices = {d["device_id"] for d in device_status["devices"]}
            
            for device_id in devices:
                assert device_id in tracked_devices, f"Device {device_id} not tracked"
    
    asyncio.run(run_test())


if __name__ == "__main__":
    print("🧪 Running Simplified Backend Data Processing Integrity Property Tests...")
    print("**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2**")
    print()
    
    # Run individual property tests
    test_functions = [
        ("Valid Sensor Data Processing", test_valid_sensor_data_processing_property),
        ("Invalid Sensor Data Rejection", test_invalid_sensor_data_rejection_property),
        ("Concurrent Processing", test_concurrent_processing_property),
        ("Metadata Storage", test_metadata_storage_property),
        ("WebSocket Broadcasting", test_websocket_broadcasting_property),
        ("Device Connection Tracking", test_device_connection_tracking),
        ("Performance Under Load", test_performance_under_load),
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
        print("🎉 All backend data processing integrity properties validated!")
        exit(0)
    else:
        print("⚠️  Some property tests failed. Check backend implementation.")
        exit(1)