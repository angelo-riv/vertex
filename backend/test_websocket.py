#!/usr/bin/env python3
"""
WebSocket functionality test for ESP32 sensor data broadcasting
Tests the WebSocket connection, sensor data broadcasting, and connection management
"""

import asyncio
import websockets
import json
import requests
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws/sensor-stream"

async def test_websocket_connection():
    """Test basic WebSocket connection and message handling"""
    print("🔌 Testing WebSocket connection...")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ WebSocket connection established")
            
            # Wait for connection confirmation
            initial_message = await websocket.recv()
            initial_data = json.loads(initial_message)
            print(f"📨 Received initial message: {initial_data['type']}")
            
            # Send ping message
            ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
            await websocket.send(json.dumps(ping_message))
            print("📤 Sent ping message")
            
            # Wait for pong response
            pong_response = await websocket.recv()
            pong_data = json.loads(pong_response)
            print(f"📥 Received pong: {pong_data['type']}")
            
            # Request device status
            status_request = {"type": "request_device_status"}
            await websocket.send(json.dumps(status_request))
            print("📤 Requested device status")
            
            # Wait for device status response
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            print(f"📥 Device status: {len(status_data.get('devices', []))} devices")
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {str(e)}")
        return False

def test_sensor_data_endpoint():
    """Test sensor data endpoint and verify WebSocket broadcasting"""
    print("\n🔬 Testing sensor data endpoint...")
    
    # Test sensor data payload
    test_data = {
        "deviceId": "ESP32_TEST_001",
        "timestamp": int(time.time() * 1000),  # Current timestamp in milliseconds
        "pitch": -12.5,
        "fsrLeft": 512,
        "fsrRight": 768
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/sensor-data", json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Sensor data endpoint working")
            print(f"📊 Processed data: tilt={result['processed_data']['tilt_angle']}°, "
                  f"direction={result['processed_data']['tilt_direction']}")
            print(f"🔗 WebSocket broadcast: {result.get('websocket_broadcast', False)}")
            print(f"👥 Clients notified: {result.get('clients_notified', 0)}")
            return True
        else:
            print(f"❌ Sensor data endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Sensor data test failed: {str(e)}")
        return False

async def test_real_time_broadcasting():
    """Test real-time sensor data broadcasting via WebSocket"""
    print("\n📡 Testing real-time broadcasting...")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✅ WebSocket connected for broadcasting test")
            
            # Wait for initial connection message
            await websocket.recv()
            
            # Send sensor data via HTTP API in a separate task
            def send_sensor_data():
                test_data = {
                    "deviceId": "ESP32_BROADCAST_TEST",
                    "timestamp": int(time.time() * 1000),
                    "pitch": 8.3,
                    "fsrLeft": 300,
                    "fsrRight": 900
                }
                
                response = requests.post(f"{BACKEND_URL}/api/sensor-data", json=test_data)
                return response.status_code == 200
            
            # Send sensor data
            print("📤 Sending sensor data via HTTP...")
            success = send_sensor_data()
            
            if not success:
                print("❌ Failed to send sensor data")
                return False
            
            # Wait for WebSocket broadcast (with timeout)
            try:
                broadcast_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                broadcast_data = json.loads(broadcast_message)
                
                if broadcast_data.get("type") == "sensor_data":
                    print("✅ Received real-time sensor data broadcast")
                    print(f"📊 Broadcast data: device={broadcast_data['data']['device_id']}, "
                          f"tilt={broadcast_data['data']['processed_data']['tilt_angle']}°")
                    return True
                else:
                    print(f"❌ Unexpected message type: {broadcast_data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for WebSocket broadcast")
                return False
            
    except Exception as e:
        print(f"❌ Broadcasting test failed: {str(e)}")
        return False

def test_websocket_stats():
    """Test WebSocket statistics endpoint"""
    print("\n📈 Testing WebSocket statistics...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/websocket/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ WebSocket stats endpoint working")
            print(f"🔗 Total connections: {stats['websocket_connections']['total_connections']}")
            print(f"📱 Connected devices: {stats['device_connections']['connected_devices']}")
            print(f"🚀 Real-time broadcasting: {stats['system_status']['real_time_broadcasting']}")
            return True
        else:
            print(f"❌ WebSocket stats failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket stats test failed: {str(e)}")
        return False

async def main():
    """Run all WebSocket tests"""
    print("🧪 Starting WebSocket functionality tests...\n")
    
    # Test basic functionality
    tests_passed = 0
    total_tests = 4
    
    # Test 1: WebSocket connection
    if await test_websocket_connection():
        tests_passed += 1
    
    # Test 2: Sensor data endpoint
    if test_sensor_data_endpoint():
        tests_passed += 1
    
    # Test 3: Real-time broadcasting
    if await test_real_time_broadcasting():
        tests_passed += 1
    
    # Test 4: WebSocket statistics
    if test_websocket_stats():
        tests_passed += 1
    
    # Summary
    print(f"\n📋 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All WebSocket tests passed! Real-time broadcasting is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    exit(0 if success else 1)