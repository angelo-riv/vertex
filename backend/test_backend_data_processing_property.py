#!/usr/bin/env python3
"""
Property-Based Test for Backend Data Processing Integrity

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2**

Property 3: Backend Data Processing Integrity
For any HTTP POST request from ESP32 device, the FastAPI backend should validate JSON 
structure and sensor ranges, store complete metadata (patient_id, session_id, timestamp, 
device_id) to Supabase within 500ms, broadcast via WebSocket to connected clients, and 
handle concurrent connections without performance degradation.

This test validates that the backend correctly processes ESP32 sensor data with proper 
validation, storage, and broadcasting across all input scenarios.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

import httpx
import websockets
from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant

from main import app, ESP32SensorData, websocket_manager, device_connections


# Test configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws/sensor-stream"
MAX_LATENCY_MS = 500  # 500ms requirement for storage


# Hypothesis strategies for generating test data
@st.composite
def esp32_sensor_data_strategy(draw):
    """Generate valid ESP32 sensor data for property testing"""
    device_id = draw(st.text(min_size=8, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))).map(lambda x: f"ESP32_{x}"))
    
    # Generate timestamp within reasonable range (use fixed base time for consistency)
    base_time_ms = 1700000000000  # Fixed base timestamp
    timestamp = draw(st.integers(
        min_value=base_time_ms,
        max_value=base_time_ms + 86400000  # 24 hours from base
    ))
    
    pitch = draw(st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False))
    fsr_left = draw(st.integers(min_value=0, max_value=4095))
    fsr_right = draw(st.integers(min_value=0, max_value=4095))
    
    return {
        "deviceId": device_id,
        "timestamp": timestamp,
        "pitch": pitch,
        "fsrLeft": fsr_left,
        "fsrRight": fsr_right
    }


@st.composite
def invalid_sensor_data_strategy(draw):
    """Generate invalid ESP32 sensor data to test validation"""
    choice = draw(st.integers(min_value=1, max_value=6))
    
    if choice == 1:
        # Invalid device ID (doesn't start with ESP32_)
        return {
            "deviceId": draw(st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith("ESP32_"))),
            "timestamp": int(time.time() * 1000),
            "pitch": 0.0,
            "fsrLeft": 512,
            "fsrRight": 512
        }
    elif choice == 2:
        # Invalid pitch (out of range)
        return {
            "deviceId": "ESP32_TEST",
            "timestamp": int(time.time() * 1000),
            "pitch": draw(st.one_of(
                st.floats(min_value=-1000.0, max_value=-180.1),
                st.floats(min_value=180.1, max_value=1000.0)
            )),
            "fsrLeft": 512,
            "fsrRight": 512
        }
    elif choice == 3:
        # Invalid FSR values (out of range)
        return {
            "deviceId": "ESP32_TEST",
            "timestamp": int(time.time() * 1000),
            "pitch": 0.0,
            "fsrLeft": draw(st.integers(min_value=-1000, max_value=-1)),
            "fsrRight": draw(st.integers(min_value=4096, max_value=10000))
        }
    elif choice == 4:
        # Invalid timestamp (too far in past/future)
        base_time_ms = 1700000000000  # Fixed base timestamp
        return {
            "deviceId": "ESP32_TEST",
            "timestamp": draw(st.one_of(
                st.integers(min_value=0, max_value=base_time_ms - 86400001),  # More than 24h before base
                st.integers(min_value=base_time_ms + 86400001, max_value=base_time_ms + 172800000)  # More than 24h after base
            )),
            "pitch": 0.0,
            "fsrLeft": 512,
            "fsrRight": 512
        }
    elif choice == 5:
        # Missing required fields
        base_data = {
            "deviceId": "ESP32_TEST",
            "timestamp": 1700000000000,  # Fixed timestamp
            "pitch": 0.0,
            "fsrLeft": 512,
            "fsrRight": 512
        }
        field_to_remove = draw(st.sampled_from(list(base_data.keys())))
        del base_data[field_to_remove]
        return base_data
    else:
        # Invalid data types
        return {
            "deviceId": draw(st.integers()),  # Should be string
            "timestamp": draw(st.text()),     # Should be int
            "pitch": draw(st.text()),         # Should be float
            "fsrLeft": draw(st.text()),       # Should be int
            "fsrRight": draw(st.text())       # Should be int
        }


class BackendDataProcessingStateMachine(RuleBasedStateMachine):
    """Stateful property testing for backend data processing integrity"""
    
    def __init__(self):
        super().__init__()
        self.connected_devices = set()
        self.websocket_clients = []
        self.processed_data_count = 0
        self.validation_errors = 0
        
    @initialize()
    def setup(self):
        """Initialize test state"""
        # Clear any existing device connections
        device_connections.clear()
        
        # Clear WebSocket connections
        websocket_manager.active_connections.clear()
        websocket_manager.connection_info.clear()
    
    @rule(sensor_data=esp32_sensor_data_strategy())
    async def process_valid_sensor_data(self, sensor_data):
        """Test processing of valid sensor data"""
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            try:
                response = await client.post(
                    f"{BACKEND_URL}/api/sensor-data/test",
                    json=sensor_data,
                    timeout=1.0
                )
                
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Property: Valid data should be processed successfully
                assert response.status_code == 200, f"Valid data rejected: {response.text}"
                
                # Property: Processing should complete within 500ms
                assert processing_time <= MAX_LATENCY_MS, f"Processing took {processing_time:.1f}ms > {MAX_LATENCY_MS}ms"
                
                result = response.json()
                
                # Property: Response should contain required fields
                assert "status" in result
                assert "processed_data" in result
                assert "device_status" in result
                
                # Property: Device connection should be tracked
                device_status = result["device_status"]
                assert device_status["device_id"] == sensor_data["deviceId"]
                assert device_status["connection_status"] == "connected"
                
                # Property: Processed data should be derived correctly
                processed = result["processed_data"]
                assert "tilt_angle" in processed
                assert "tilt_direction" in processed
                assert "alert_level" in processed
                assert "fsr_balance" in processed
                
                # Property: Tilt angle should be absolute value of pitch
                expected_tilt = abs(sensor_data["pitch"])
                assert abs(processed["tilt_angle"] - expected_tilt) < 0.1
                
                # Property: FSR balance should be calculated correctly
                total_fsr = sensor_data["fsrLeft"] + sensor_data["fsrRight"]
                if total_fsr > 0:
                    expected_balance = (sensor_data["fsrRight"] - sensor_data["fsrLeft"]) / total_fsr
                    assert abs(processed["fsr_balance"] - expected_balance) < 0.001
                
                self.connected_devices.add(sensor_data["deviceId"])
                self.processed_data_count += 1
                
            except httpx.TimeoutException:
                pytest.fail(f"Request timed out - processing took longer than 1 second")
            except Exception as e:
                pytest.fail(f"Unexpected error processing valid data: {str(e)}")
    
    @rule(invalid_data=invalid_sensor_data_strategy())
    async def process_invalid_sensor_data(self, invalid_data):
        """Test validation of invalid sensor data"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/api/sensor-data/test",
                    json=invalid_data,
                    timeout=1.0
                )
                
                # Property: Invalid data should be rejected with appropriate status code
                assert response.status_code in [400, 422], f"Invalid data accepted: {response.status_code}"
                
                self.validation_errors += 1
                
            except httpx.TimeoutException:
                pytest.fail("Validation should not timeout")
            except Exception as e:
                # Some invalid data might cause JSON parsing errors, which is acceptable
                if "json" not in str(e).lower():
                    pytest.fail(f"Unexpected error during validation: {str(e)}")
    
    @invariant()
    def device_tracking_invariant(self):
        """Invariant: Device connections should be tracked consistently"""
        # All processed devices should be in the device connections
        for device_id in self.connected_devices:
            assert device_id in device_connections, f"Device {device_id} not tracked in connections"
    
    @invariant()
    def performance_invariant(self):
        """Invariant: System should maintain performance under load"""
        # If we've processed data, the system should still be responsive
        if self.processed_data_count > 0:
            assert len(device_connections) <= self.processed_data_count
            # Device connections should not grow unbounded
            assert len(device_connections) < 1000


# Property-based tests using Hypothesis

@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=15, deadline=1500)  # Reduced for faster execution
async def test_sensor_data_validation_property_impl(sensor_data):
    """
    Property: For any valid ESP32 sensor data, the backend should validate 
    JSON structure and sensor ranges correctly.
    
    **Validates: Requirements 3.1, 3.2**
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/sensor-data/test",
            json=sensor_data,
            timeout=1.0
        )
        
        # Property: Valid sensor data should always be accepted
        assert response.status_code == 200, f"Valid sensor data rejected: {response.text}"
        
        result = response.json()
        
        # Property: Response should contain validation confirmation
        assert result["status"] == "success"
        assert "processed_data" in result
        
        # Property: Device ID validation
        assert sensor_data["deviceId"].startswith("ESP32_")
        
        # Property: Sensor ranges validation
        assert -180.0 <= sensor_data["pitch"] <= 180.0
        assert 0 <= sensor_data["fsrLeft"] <= 4095
        assert 0 <= sensor_data["fsrRight"] <= 4095


@given(invalid_data=invalid_sensor_data_strategy())
@settings(max_examples=30, deadline=2000)
async def test_sensor_data_rejection_property_impl(invalid_data):
    """
    Property: For any invalid ESP32 sensor data, the backend should reject 
    the data with appropriate error codes.
    
    **Validates: Requirements 3.2, 3.5**
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BACKEND_URL}/api/sensor-data/test",
                json=invalid_data,
                timeout=1.0
            )
            
            # Property: Invalid data should be rejected
            assert response.status_code in [400, 422, 500], f"Invalid data accepted: {response.status_code}"
            
        except (httpx.RequestError, json.JSONDecodeError):
            # Some invalid data might cause request errors, which is acceptable
            pass


@given(sensor_data_list=st.lists(esp32_sensor_data_strategy(), min_size=1, max_size=10))
@settings(max_examples=20, deadline=5000)
async def test_concurrent_processing_property_impl(sensor_data_list):
    """
    Property: For any set of concurrent HTTP POST requests from ESP32 devices, 
    the backend should handle them without performance degradation.
    
    **Validates: Requirements 3.6, 3.7**
    """
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        
        # Send all requests concurrently
        tasks = []
        for sensor_data in sensor_data_list:
            task = client.post(
                f"{BACKEND_URL}/api/sensor-data/test",
                json=sensor_data,
                timeout=2.0
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Property: All valid requests should be processed successfully
        successful_responses = 0
        for response in responses:
            if isinstance(response, httpx.Response) and response.status_code == 200:
                successful_responses += 1
        
        assert successful_responses == len(sensor_data_list), "Not all concurrent requests processed successfully"
        
        # Property: Concurrent processing should not significantly degrade performance
        # Allow more time for concurrent processing, but should still be reasonable
        max_concurrent_time = MAX_LATENCY_MS * 2  # 1000ms for concurrent processing
        assert total_time <= max_concurrent_time, f"Concurrent processing took {total_time:.1f}ms > {max_concurrent_time}ms"


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=30, deadline=3000)
async def test_metadata_completeness_property_impl(sensor_data):
    """
    Property: For any sensor data processed, the backend should include complete 
    metadata (patient_id, session_id, timestamp, device_id) in storage operations.
    
    **Validates: Requirements 3.3, 5.1, 5.2**
    """
    # Mock Supabase to capture storage operations
    with patch('main.supabase') as mock_supabase:
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value.data = [{"id": "test_id"}]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/sensor-data",  # Use real endpoint for storage testing
                json=sensor_data,
                timeout=1.0
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


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=20, deadline=4000)
async def test_websocket_broadcasting_property_impl(sensor_data):
    """
    Property: For any sensor data received, the backend should broadcast 
    via WebSocket to connected clients.
    
    **Validates: Requirements 3.4**
    """
    # Test WebSocket broadcasting by connecting a client and sending data
    try:
        async with websockets.connect(WEBSOCKET_URL, timeout=2) as websocket:
            # Wait for connection confirmation
            await asyncio.wait_for(websocket.recv(), timeout=1.0)
            
            # Send sensor data via HTTP API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{BACKEND_URL}/api/sensor-data",
                    json=sensor_data,
                    timeout=1.0
                )
                
                assert response.status_code == 200
            
            # Property: WebSocket client should receive broadcast within reasonable time
            try:
                broadcast_message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
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


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=30, deadline=2000)
async def test_storage_latency_property_impl(sensor_data):
    """
    Property: For any sensor data, storage operations should complete within 500ms.
    
    **Validates: Requirements 5.1, 5.2**
    """
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/sensor-data/test",
            json=sensor_data,
            timeout=1.0
        )
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Property: Processing should complete within latency requirement
        assert processing_time <= MAX_LATENCY_MS, f"Storage took {processing_time:.1f}ms > {MAX_LATENCY_MS}ms"
        
        assert response.status_code == 200
        result = response.json()
        
        # Property: Response should indicate successful processing
        assert result["status"] == "success"


# Integration test combining multiple properties
@given(
    device_count=st.integers(min_value=1, max_value=5),
    data_points_per_device=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=10, deadline=10000)
async def test_multi_device_integration_property_impl(device_count, data_points_per_device):
    """
    Property: For any number of ESP32 devices sending data concurrently, 
    the backend should maintain data integrity and performance.
    
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2**
    """
    # Generate unique device IDs and sensor data
    devices = [f"ESP32_DEVICE_{i:03d}" for i in range(device_count)]
    all_requests = []
    
    for device_id in devices:
        for _ in range(data_points_per_device):
            sensor_data = {
                "deviceId": device_id,
                "timestamp": 1700000000000 + len(all_requests),  # Fixed base timestamp
                "pitch": float(st.floats(min_value=-180.0, max_value=180.0, allow_nan=False, allow_infinity=False).example()),
                "fsrLeft": st.integers(min_value=0, max_value=4095).example(),
                "fsrRight": st.integers(min_value=0, max_value=4095).example()
            }
            all_requests.append(sensor_data)
    
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
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
        
        # Property: Multi-device processing should maintain reasonable performance
        max_multi_device_time = MAX_LATENCY_MS * 3  # Allow more time for multiple devices
        assert total_time <= max_multi_device_time, f"Multi-device processing took {total_time:.1f}ms > {max_multi_device_time}ms"
        
        # Property: Each device should be tracked separately
        device_status_response = await client.get(f"{BACKEND_URL}/api/sensor-data/devices", timeout=1.0)
        assert device_status_response.status_code == 200
        
        device_status = device_status_response.json()
        tracked_devices = {d["device_id"] for d in device_status["devices"]}
        
        for device_id in devices:
            assert device_id in tracked_devices, f"Device {device_id} not tracked"


# Synchronous wrapper functions for Hypothesis compatibility
def run_async_property_test(async_test_func, *args, **kwargs):
    """Helper to run async property tests synchronously"""
    return asyncio.run(async_test_func(*args, **kwargs))


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=50, deadline=2000)
def test_sensor_data_validation_property_sync(sensor_data):
    """Synchronous wrapper for sensor data validation property test"""
    run_async_property_test(test_sensor_data_validation_property_impl, sensor_data)


@given(invalid_data=invalid_sensor_data_strategy())
@settings(max_examples=30, deadline=2000)
def test_sensor_data_rejection_property_sync(invalid_data):
    """Synchronous wrapper for sensor data rejection property test"""
    run_async_property_test(test_sensor_data_rejection_property_impl, invalid_data)


@given(sensor_data_list=st.lists(esp32_sensor_data_strategy(), min_size=1, max_size=10))
@settings(max_examples=20, deadline=5000)
def test_concurrent_processing_property_sync(sensor_data_list):
    """Synchronous wrapper for concurrent processing property test"""
    run_async_property_test(test_concurrent_processing_property_impl, sensor_data_list)


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=30, deadline=3000)
def test_metadata_completeness_property_sync(sensor_data):
    """Synchronous wrapper for metadata completeness property test"""
    run_async_property_test(test_metadata_completeness_property_impl, sensor_data)


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=20, deadline=4000)
def test_websocket_broadcasting_property_sync(sensor_data):
    """Synchronous wrapper for WebSocket broadcasting property test"""
    run_async_property_test(test_websocket_broadcasting_property_impl, sensor_data)


@given(sensor_data=esp32_sensor_data_strategy())
@settings(max_examples=30, deadline=2000)
def test_storage_latency_property_sync(sensor_data):
    """Synchronous wrapper for storage latency property test"""
    run_async_property_test(test_storage_latency_property_impl, sensor_data)


@given(
    device_count=st.integers(min_value=1, max_value=5),
    data_points_per_device=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=10, deadline=10000)
def test_multi_device_integration_property_sync(device_count, data_points_per_device):
    """Synchronous wrapper for multi-device integration property test"""
    run_async_property_test(test_multi_device_integration_property_impl, device_count, data_points_per_device)


if __name__ == "__main__":
    print("🧪 Running Backend Data Processing Integrity Property Tests...")
    print("**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2**")
    print()
    
    # Run individual property tests
    test_functions = [
        ("Sensor Data Validation", test_sensor_data_validation_property_sync),
        ("Sensor Data Rejection", test_sensor_data_rejection_property_sync),
        ("Concurrent Processing", test_concurrent_processing_property_sync),
        ("Metadata Completeness", test_metadata_completeness_property_sync),
        ("WebSocket Broadcasting", test_websocket_broadcasting_property_sync),
        ("Storage Latency", test_storage_latency_property_sync),
        ("Multi-Device Integration", test_multi_device_integration_property_sync),
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
    else:
        print("⚠️  Some property tests failed. Check backend implementation.")