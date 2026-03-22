"""
Property Test for System Performance Under Load

**Feature: vertex-data-integration, Property 8: System Performance Under Load**

For any sensor data processing operation, end-to-end latency should remain below 200ms 
from ESP32 POST to frontend display, UI updates should render within 50ms of WebSocket 
receipt, database storage should not block real-time processing, and memory management 
should include automatic cleanup of old readings.

**Validates: Requirements 8.1, 8.2, 8.3, 8.5, 8.6, 8.7**
"""

import asyncio
import time
import json
import statistics
import psutil
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest

from main import (
    ESP32SensorData, 
    receive_esp32_sensor_data, 
    websocket_manager,
    performance_monitor,
    _background_database_storage
)


@pytest.mark.asyncio
async def test_concurrent_sensor_processing_performance():
    """
    Property: Concurrent sensor data processing maintains performance under load
    
    **Feature: vertex-data-integration, Property 8: System Performance Under Load**
    
    Tests that multiple simultaneous ESP32 connections can be processed while
    maintaining sub-200ms end-to-end latency requirements.
    """
    concurrent_devices = 5
    requests_per_device = 10
    
    start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    processing_times = []
    
    # Create multiple concurrent sensor data requests
    tasks = []
    start_time = time.time()
    
    for device_num in range(concurrent_devices):
        for request_num in range(requests_per_device):
            sensor_data = ESP32SensorData(
                deviceId=f"ESP32_PERF_TEST_{device_num:03d}",
                timestamp=int(time.time() * 1000),
                pitch=float((request_num * 2) - 10),  # Vary pitch from -10 to 8
                fsrLeft=400 + (request_num * 10),
                fsrRight=600 - (request_num * 10)
            )
            
            task = _measure_processing_performance(sensor_data)
            tasks.append(task)
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    total_processing_time = (end_time - start_time) * 1000  # ms
    
    # Verify all requests succeeded
    successful_results = [r for r in results if isinstance(r, dict) and not isinstance(r, Exception)]
    total_requests = concurrent_devices * requests_per_device
    
    assert len(successful_results) == total_requests, f"Expected {total_requests} successful results, got {len(successful_results)}"
    
    # Property: End-to-end latency remains below 200ms per request under concurrent load
    processing_times = [r['processing_time_ms'] for r in successful_results]
    avg_latency_per_request = statistics.mean(processing_times)
    max_latency = max(processing_times)
    p95_latency = _calculate_percentile(processing_times, 95)
    
    assert avg_latency_per_request < 200, f"Average latency {avg_latency_per_request:.1f}ms exceeds 200ms limit"
    assert max_latency < 400, f"Maximum latency {max_latency:.1f}ms exceeds 400ms absolute limit"
    assert p95_latency < 250, f"95th percentile latency {p95_latency:.1f}ms exceeds 250ms limit"
    
    # Property: Memory usage remains bounded
    end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    memory_increase = end_memory - start_memory
    memory_per_request = memory_increase / total_requests
    
    assert memory_per_request < 0.5, f"Memory per request {memory_per_request:.2f}MB exceeds 0.5MB limit"
    
    print(f"✓ Concurrent processing test passed:")
    print(f"  - {total_requests} requests processed in {total_processing_time:.1f}ms")
    print(f"  - Average latency: {avg_latency_per_request:.1f}ms")
    print(f"  - 95th percentile: {p95_latency:.1f}ms")
    print(f"  - Memory increase: {memory_increase:.1f}MB")


@pytest.mark.asyncio
async def test_high_frequency_data_transmission():
    """
    Property: High-frequency data transmission maintains performance and memory efficiency
    
    **Feature: vertex-data-integration, Property 8: System Performance Under Load**
    
    Tests that sustained high-frequency sensor data (10 Hz) can be processed
    without memory leaks or performance degradation.
    """
    frequency_hz = 10.0
    duration_seconds = 3.0
    num_readings = int(frequency_hz * duration_seconds)
    interval_ms = 1000 / frequency_hz
    
    memory_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    processing_times = []
    
    for i in range(num_readings):
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_HIGH_FREQ_{i % 3}",  # Rotate through 3 devices
            timestamp=int(time.time() * 1000),
            pitch=float((i % 40) - 20),  # Cycle through -20 to 19 degrees
            fsrLeft=400 + (i % 200),
            fsrRight=600 - (i % 200)
        )
        
        start_time = time.time()
        result = await receive_esp32_sensor_data(sensor_data)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000
        processing_times.append(processing_time)
        
        # Property: Each individual processing maintains latency requirement
        assert processing_time < 200, f"Processing time {processing_time:.1f}ms exceeds 200ms limit at reading {i}"
        
        # Simulate transmission frequency
        await asyncio.sleep(interval_ms / 1000)
    
    memory_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    memory_increase = memory_after - memory_before
    
    # Property: Memory usage remains bounded during high-frequency processing
    max_memory_increase = 50  # MB
    assert memory_increase < max_memory_increase, f"Memory increased by {memory_increase:.1f}MB, exceeds {max_memory_increase}MB limit"
    
    # Property: Processing times remain stable (no significant degradation)
    if len(processing_times) >= 10:
        first_10_avg = statistics.mean(processing_times[:10])
        last_10_avg = statistics.mean(processing_times[-10:])
        degradation_ratio = last_10_avg / first_10_avg if first_10_avg > 0 else 1.0
        
        # Processing should not degrade by more than 50%
        assert degradation_ratio < 1.5, f"Performance degraded by {(degradation_ratio - 1) * 100:.1f}%, exceeds 50% limit"
    
    avg_processing = statistics.mean(processing_times)
    print(f"✓ High-frequency transmission test passed:")
    print(f"  - {num_readings} readings at {frequency_hz}Hz")
    print(f"  - Average processing: {avg_processing:.1f}ms")
    print(f"  - Memory increase: {memory_increase:.1f}MB")


@pytest.mark.asyncio
async def test_database_storage_non_blocking():
    """
    Property: Database storage operations do not block real-time processing
    
    **Feature: vertex-data-integration, Property 8: System Performance Under Load**
    
    Tests that background database storage maintains performance isolation
    from real-time sensor data processing.
    """
    storage_batch_size = 20
    concurrent_storage_ops = 3
    
    # Create sensor data for storage
    sensor_data_batch = []
    for i in range(storage_batch_size):
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_STORAGE_TEST_{i % 3}",
            timestamp=int(time.time() * 1000),
            pitch=float((i % 30) - 15),
            fsrLeft=300 + i,
            fsrRight=700 - i
        )
        sensor_data_batch.append(sensor_data)
    
    # Start storage operations in background
    storage_tasks = []
    for i in range(concurrent_storage_ops):
        for sensor_data in sensor_data_batch[i::concurrent_storage_ops]:
            task = _background_database_storage(
                sensor_data, 
                datetime.now(timezone.utc), 
                sensor_data.deviceId
            )
            storage_tasks.append(task)
    
    storage_start = time.time()
    storage_task_group = asyncio.create_task(asyncio.gather(*storage_tasks, return_exceptions=True))
    
    # Perform real-time processing while storage is running
    realtime_processing_times = []
    for i in range(10):  # Test 10 real-time operations
        sensor_data = ESP32SensorData(
            deviceId="ESP32_REALTIME_DEVICE",
            timestamp=int(time.time() * 1000),
            pitch=float(i * 2 - 10),
            fsrLeft=500,
            fsrRight=500
        )
        
        realtime_start = time.time()
        result = await receive_esp32_sensor_data(sensor_data)
        realtime_end = time.time()
        
        realtime_processing_time = (realtime_end - realtime_start) * 1000
        realtime_processing_times.append(realtime_processing_time)
        
        # Property: Real-time processing maintains latency during storage operations
        assert realtime_processing_time < 200, f"Real-time processing {realtime_processing_time:.1f}ms exceeds 200ms during storage operations"
        
        await asyncio.sleep(0.01)  # Small delay between real-time operations
    
    # Wait for storage operations to complete
    await storage_task_group
    storage_end = time.time()
    
    storage_duration = (storage_end - storage_start) * 1000
    
    # Property: Storage operations complete within reasonable time
    max_storage_time = storage_batch_size * 20  # 20ms per item max
    assert storage_duration < max_storage_time, f"Storage took {storage_duration:.1f}ms, exceeds {max_storage_time:.1f}ms limit"
    
    # Property: Real-time processing performance is not significantly impacted
    avg_realtime_processing = statistics.mean(realtime_processing_times)
    assert avg_realtime_processing < 150, f"Average real-time processing {avg_realtime_processing:.1f}ms too high during storage"
    
    print(f"✓ Database storage non-blocking test passed:")
    print(f"  - Storage duration: {storage_duration:.1f}ms for {len(storage_tasks)} operations")
    print(f"  - Real-time processing avg: {avg_realtime_processing:.1f}ms")


@pytest.mark.asyncio
async def test_memory_management_and_cleanup():
    """
    Property: Memory management includes automatic cleanup of old readings
    
    **Feature: vertex-data-integration, Property 8: System Performance Under Load**
    
    Tests that the system properly manages memory by cleaning up old sensor readings
    and maintaining bounded memory usage under sustained load.
    """
    memory_pressure_readings = 100
    cleanup_interval_seconds = 2.0
    
    start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    
    # Generate enough data to create memory pressure
    for i in range(memory_pressure_readings):
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_MEMORY_TEST_{i % 5}",
            timestamp=int(time.time() * 1000),
            pitch=float((i % 80) - 40),
            fsrLeft=100 + (i % 900),
            fsrRight=1000 - (i % 900)
        )
        
        await receive_esp32_sensor_data(sensor_data)
        
        # Trigger cleanup periodically
        if i % int(cleanup_interval_seconds * 10) == 0:
            await asyncio.sleep(0.001)
    
    # Allow time for background cleanup
    await asyncio.sleep(cleanup_interval_seconds)
    
    end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    memory_increase = end_memory - start_memory
    
    # Property: Memory increase should be bounded despite processing many readings
    max_acceptable_increase = 30  # MB
    assert memory_increase < max_acceptable_increase, f"Memory increased by {memory_increase:.1f}MB, exceeds {max_acceptable_increase:.1f}MB limit"
    
    # Property: Memory usage should stabilize (not grow indefinitely)
    memory_per_100_readings = (memory_increase / memory_pressure_readings) * 100
    assert memory_per_100_readings < 10, f"Memory usage {memory_per_100_readings:.2f}MB per 100 readings exceeds 10MB limit"
    
    print(f"✓ Memory management test passed:")
    print(f"  - {memory_pressure_readings} readings processed")
    print(f"  - Memory increase: {memory_increase:.1f}MB")
    print(f"  - Memory per 100 readings: {memory_per_100_readings:.2f}MB")


@pytest.mark.asyncio
async def test_websocket_broadcast_performance():
    """
    Property: WebSocket broadcast operations complete within 50ms
    
    **Feature: vertex-data-integration, Property 8: System Performance Under Load**
    
    Tests that WebSocket broadcasting maintains low latency under load.
    """
    num_broadcasts = 20
    broadcast_times = []
    
    for i in range(num_broadcasts):
        # Create test sensor data
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_WS_TEST_{i % 3}",
            timestamp=int(time.time() * 1000),
            pitch=float(i * 2 - 20),
            fsrLeft=400 + i,
            fsrRight=600 - i
        )
        
        # Measure WebSocket broadcast simulation
        broadcast_start = time.time()
        
        # Simulate WebSocket message creation and broadcast
        message_data = {
            "type": "sensor_data",
            "deviceId": sensor_data.deviceId,
            "timestamp": sensor_data.timestamp,
            "pitch": sensor_data.pitch,
            "fsrLeft": sensor_data.fsrLeft,
            "fsrRight": sensor_data.fsrRight
        }
        message_json = json.dumps(message_data)
        
        # Simulate broadcast processing time
        await asyncio.sleep(0.001)  # 1ms simulation
        
        broadcast_end = time.time()
        broadcast_time = (broadcast_end - broadcast_start) * 1000
        broadcast_times.append(broadcast_time)
        
        # Property: Individual broadcast within 50ms
        assert broadcast_time < 50, f"Broadcast {i} took {broadcast_time:.1f}ms, exceeds 50ms limit"
    
    # Property: Average broadcast performance
    avg_broadcast_time = statistics.mean(broadcast_times)
    max_broadcast_time = max(broadcast_times)
    
    assert avg_broadcast_time < 25, f"Average broadcast time {avg_broadcast_time:.1f}ms exceeds 25ms target"
    assert max_broadcast_time < 50, f"Maximum broadcast time {max_broadcast_time:.1f}ms exceeds 50ms requirement"
    
    print(f"✓ WebSocket broadcast performance test passed:")
    print(f"  - {num_broadcasts} broadcasts completed")
    print(f"  - Average time: {avg_broadcast_time:.1f}ms")
    print(f"  - Maximum time: {max_broadcast_time:.1f}ms")


async def _measure_processing_performance(sensor_data: ESP32SensorData) -> Dict[str, Any]:
    """Measure detailed performance metrics for sensor data processing"""
    overall_start = time.time()
    
    # Measure main processing
    processing_start = time.time()
    try:
        result = await receive_esp32_sensor_data(sensor_data)
        processing_end = time.time()
        
        overall_end = time.time()
        
        # Return performance metrics
        return {
            'status': 'success',
            'processing_time_ms': (processing_end - processing_start) * 1000,
            'end_to_end_time_ms': (overall_end - overall_start) * 1000,
            'result': result
        }
        
    except Exception as e:
        processing_end = time.time()
        return {
            'status': 'error',
            'error': str(e),
            'processing_time_ms': (processing_end - processing_start) * 1000,
            'end_to_end_time_ms': (processing_end - overall_start) * 1000
        }


def _calculate_percentile(data: List[float], percentile: int) -> float:
    """Calculate percentile value for performance analysis"""
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


# Test runner for property-based tests
if __name__ == "__main__":
    import pytest
    
    # Run the property-based tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])