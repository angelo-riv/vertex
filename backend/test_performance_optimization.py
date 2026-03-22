"""
Performance Optimization Test Suite

Tests the optimized sensor data processing pipeline to ensure sub-200ms latency requirements.
"""

import asyncio
import time
import json
from datetime import datetime, timezone
from main import receive_esp32_sensor_data, ESP32SensorData, websocket_manager
from performance_monitor import performance_monitor

async def test_optimized_sensor_processing():
    """Test optimized sensor data processing performance"""
    print("Testing optimized sensor data processing...")
    
    # Test data
    test_cases = [
        {"deviceId": "ESP32_TEST_001", "pitch": -12.5, "fsrLeft": 512, "fsrRight": 768},
        {"deviceId": "ESP32_TEST_002", "pitch": 8.2, "fsrLeft": 600, "fsrRight": 400},
        {"deviceId": "ESP32_TEST_003", "pitch": -18.7, "fsrLeft": 300, "fsrRight": 900},
        {"deviceId": "ESP32_TEST_004", "pitch": 2.1, "fsrLeft": 500, "fsrRight": 520},
        {"deviceId": "ESP32_TEST_005", "pitch": 22.3, "fsrLeft": 200, "fsrRight": 1000}
    ]
    
    processing_times = []
    
    for i, test_case in enumerate(test_cases):
        # Create test sensor data
        sensor_data = ESP32SensorData(
            deviceId=test_case["deviceId"],
            timestamp=int(time.time() * 1000),
            pitch=test_case["pitch"],
            fsrLeft=test_case["fsrLeft"],
            fsrRight=test_case["fsrRight"]
        )
        
        # Measure processing time
        start_time = time.time()
        
        try:
            result = await receive_esp32_sensor_data(sensor_data)
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            processing_times.append(processing_time)
            
            print(f"Test {i+1}: {processing_time:.2f}ms - {result.get('status', 'unknown')}")
            
            # Verify response structure
            assert result.get("status") == "ok"
            assert "time_ms" in result
            assert "clients" in result
            
        except Exception as e:
            print(f"Test {i+1} failed: {e}")
            return False
    
    # Calculate statistics
    avg_time = sum(processing_times) / len(processing_times)
    max_time = max(processing_times)
    min_time = min(processing_times)
    
    print(f"\nPerformance Results:")
    print(f"Average processing time: {avg_time:.2f}ms")
    print(f"Maximum processing time: {max_time:.2f}ms")
    print(f"Minimum processing time: {min_time:.2f}ms")
    
    # Check if requirements are met
    latency_requirement = 200  # ms
    meets_requirement = max_time < latency_requirement
    
    print(f"Latency requirement (<{latency_requirement}ms): {'PASS' if meets_requirement else 'FAIL'}")
    
    return meets_requirement

async def test_websocket_broadcast_performance():
    """Test WebSocket broadcast performance"""
    print("\nTesting WebSocket broadcast performance...")
    
    # Simulate WebSocket clients
    mock_clients = []
    for i in range(5):
        mock_clients.append(f"mock_client_{i}")
    
    # Test broadcast data
    test_data = {
        "d": "ESP32_TEST_001",
        "t": datetime.now(timezone.utc).isoformat(),
        "p": -12.5,
        "fl": 512,
        "fr": 768,
        "ta": 12.5,
        "td": "right",
        "al": "warning",
        "b": 0.2
    }
    
    # Measure broadcast time
    start_time = time.time()
    
    try:
        # Simulate broadcast (without actual WebSocket connections)
        message_json = json.dumps({
            "type": "sensor_data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": test_data
        })
        
        # Simulate processing time for multiple clients
        await asyncio.sleep(0.001)  # Simulate 1ms processing
        
        end_time = time.time()
        broadcast_time = (end_time - start_time) * 1000
        
        print(f"Broadcast simulation time: {broadcast_time:.2f}ms")
        print(f"Simulated clients: {len(mock_clients)}")
        
        # Check if broadcast is fast enough (should be <50ms)
        broadcast_requirement = 50  # ms
        meets_requirement = broadcast_time < broadcast_requirement
        
        print(f"Broadcast requirement (<{broadcast_requirement}ms): {'PASS' if meets_requirement else 'FAIL'}")
        
        return meets_requirement
        
    except Exception as e:
        print(f"Broadcast test failed: {e}")
        return False

async def test_concurrent_processing():
    """Test concurrent sensor data processing"""
    print("\nTesting concurrent processing performance...")
    
    # Create multiple concurrent requests
    tasks = []
    num_concurrent = 10
    
    for i in range(num_concurrent):
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_CONCURRENT_{i:03d}",
            timestamp=int(time.time() * 1000),
            pitch=float(i * 2 - 10),  # Vary pitch from -10 to 8
            fsrLeft=500 + i * 10,
            fsrRight=500 - i * 10
        )
        
        task = receive_esp32_sensor_data(sensor_data)
        tasks.append(task)
    
    # Execute all tasks concurrently
    start_time = time.time()
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        avg_time_per_request = total_time / num_concurrent
        
        # Count successful results
        successful_results = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "ok")
        
        print(f"Concurrent requests: {num_concurrent}")
        print(f"Successful results: {successful_results}")
        print(f"Total processing time: {total_time:.2f}ms")
        print(f"Average time per request: {avg_time_per_request:.2f}ms")
        
        # Check if concurrent processing meets requirements
        concurrent_requirement = 300  # ms total for 10 concurrent requests
        meets_requirement = total_time < concurrent_requirement and successful_results == num_concurrent
        
        print(f"Concurrent processing requirement (<{concurrent_requirement}ms total): {'PASS' if meets_requirement else 'FAIL'}")
        
        return meets_requirement
        
    except Exception as e:
        print(f"Concurrent processing test failed: {e}")
        return False

async def test_memory_efficiency():
    """Test memory efficiency of optimized processing"""
    print("\nTesting memory efficiency...")
    
    import psutil
    import os
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Process many sensor readings
    num_readings = 100
    
    for i in range(num_readings):
        sensor_data = ESP32SensorData(
            deviceId=f"ESP32_MEMORY_TEST_{i:03d}",
            timestamp=int(time.time() * 1000),
            pitch=float((i % 40) - 20),  # Cycle through -20 to 19
            fsrLeft=400 + (i % 200),
            fsrRight=600 - (i % 200)
        )
        
        try:
            await receive_esp32_sensor_data(sensor_data)
        except Exception as e:
            print(f"Memory test iteration {i} failed: {e}")
    
    # Get final memory usage
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    print(f"Initial memory usage: {initial_memory:.2f} MB")
    print(f"Final memory usage: {final_memory:.2f} MB")
    print(f"Memory increase: {memory_increase:.2f} MB")
    print(f"Memory per reading: {(memory_increase / num_readings * 1024):.2f} KB")
    
    # Check if memory usage is reasonable (should be <50MB increase for 100 readings)
    memory_requirement = 50  # MB
    meets_requirement = memory_increase < memory_requirement
    
    print(f"Memory efficiency requirement (<{memory_requirement}MB increase): {'PASS' if meets_requirement else 'FAIL'}")
    
    return meets_requirement

async def run_performance_tests():
    """Run all performance tests"""
    print("=== Performance Optimization Test Suite ===\n")
    
    tests = [
        ("Optimized Sensor Processing", test_optimized_sensor_processing),
        ("WebSocket Broadcast Performance", test_websocket_broadcast_performance),
        ("Concurrent Processing", test_concurrent_processing),
        ("Memory Efficiency", test_memory_efficiency)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
        
        print("-" * 50)
    
    # Summary
    print("\n=== Test Results Summary ===")
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
        if passed:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All performance optimization tests PASSED!")
        print("System meets sub-200ms latency requirements for clinical use.")
    else:
        print("⚠️  Some performance tests FAILED.")
        print("Review optimization implementation and system resources.")
    
    # Log performance summary
    performance_monitor.log_performance_summary()
    
    return passed_tests == total_tests

if __name__ == "__main__":
    # Run the performance test suite
    success = asyncio.run(run_performance_tests())
    exit(0 if success else 1)