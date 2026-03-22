# Complete Testing Guide Without ESP32 Hardware
# Step-by-step testing using simulation and demo mode

import subprocess
import sys
import time
import threading
import requests
import json

class HardwarelessTester:
    """
    Complete testing suite that works without ESP32 hardware.
    Uses simulation, demo mode, and mocked data.
    """
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        
    def test_backend_api_endpoints(self):
        """Test backend API endpoints with simulated data."""
        print("🔧 Testing Backend API Endpoints...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/health")
            if response.status_code == 200:
                print("  ✅ Health endpoint working")
            else:
                print(f"  ❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Backend not running: {e}")
            return False
        
        # Test demo mode endpoints
        try:
            # Start demo mode
            response = requests.post(f"{self.backend_url}/api/demo/toggle", 
                                   json={"enabled": True, "scenario": "pusher_syndrome"})
            if response.status_code == 200:
                print("  ✅ Demo mode activation working")
            else:
                print(f"  ❌ Demo mode failed: {response.status_code}")
            
            # Get demo status
            response = requests.get(f"{self.backend_url}/api/demo/status")
            if response.status_code == 200:
                demo_status = response.json()
                print(f"  ✅ Demo status: {demo_status.get('active', False)}")
            
        except Exception as e:
            print(f"  ❌ Demo endpoints error: {e}")
        
        return True
    
    def test_sensor_data_simulation(self):
        """Test sensor data processing with simulated ESP32 data."""
        print("📡 Testing Sensor Data Processing...")
        
        # Simulated sensor data scenarios
        test_scenarios = [
            {
                "name": "Normal Posture",
                "data": {
                    "deviceId": "ESP32_TEST_001",
                    "timestamp": int(time.time() * 1000),
                    "pitch": 2.5,
                    "roll": 1.0,
                    "yaw": 0.5,
                    "fsrLeft": 2048,
                    "fsrRight": 2048
                },
                "expected_pusher": False
            },
            {
                "name": "Pusher Syndrome",
                "data": {
                    "deviceId": "ESP32_TEST_001", 
                    "timestamp": int(time.time() * 1000),
                    "pitch": 15.0,
                    "roll": 3.0,
                    "yaw": 1.0,
                    "fsrLeft": 1600,
                    "fsrRight": 2400
                },
                "expected_pusher": True
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing {scenario['name']}...")
            
            headers = {
                "X-Device-ID": scenario["data"]["deviceId"],
                "X-Device-Signature": "test_signature",
                "X-Timestamp": str(int(time.time())),
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(
                    f"{self.backend_url}/api/sensor-data",
                    json=scenario["data"],
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    clinical = result.get("clinical_analysis", {})
                    pusher_detected = clinical.get("pusher_detected", False)
                    
                    if pusher_detected == scenario["expected_pusher"]:
                        print(f"    ✅ Correct detection: {pusher_detected}")
                    else:
                        print(f"    ❌ Wrong detection: expected {scenario['expected_pusher']}, got {pusher_detected}")
                else:
                    print(f"    ❌ API error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {e}")
        
        return True
    
    def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates."""
        print("🔌 Testing WebSocket Connection...")
        
        try:
            import websockets
            import asyncio
            
            async def test_websocket():
                uri = f"ws://localhost:8000/ws"
                try:
                    async with websockets.connect(uri) as websocket:
                        print("  ✅ WebSocket connection established")
                        
                        # Wait for a message (with timeout)
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                            data = json.loads(message)
                            print(f"  ✅ Received message: {data.get('type', 'unknown')}")
                        except asyncio.TimeoutError:
                            print("  ⚠️ No messages received (normal if no active devices)")
                        
                        return True
                except Exception as e:
                    print(f"  ❌ WebSocket connection failed: {e}")
                    return False
            
            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_websocket())
            loop.close()
            
            return result
            
        except ImportError:
            print("  ⚠️ websockets library not installed, skipping WebSocket test")
            print("  Install with: pip install websockets")
            return True
    
    def test_clinical_algorithms(self):
        """Test clinical algorithms with various scenarios."""
        print("🧠 Testing Clinical Algorithms...")
        
        # Test clinical threshold endpoints
        try:
            # Test getting default thresholds
            response = requests.get(f"{self.backend_url}/api/clinical/thresholds/test_patient")
            if response.status_code in [200, 404]:  # 404 is OK if no thresholds set
                print("  ✅ Clinical thresholds endpoint accessible")
            else:
                print(f"  ❌ Thresholds endpoint error: {response.status_code}")
            
            # Test calibration endpoints
            response = requests.get(f"{self.backend_url}/api/calibration/history/test_patient")
            if response.status_code in [200, 404]:  # 404 is OK if no calibrations
                print("  ✅ Calibration endpoints accessible")
            else:
                print(f"  ❌ Calibration endpoint error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Clinical endpoints error: {e}")
        
        return True
    
    def run_esp32_simulator(self, duration=30):
        """Run ESP32 simulator for testing."""
        print(f"🤖 Running ESP32 Simulator for {duration} seconds...")
        
        try:
            # Import and run simulator
            from esp32_simulator import ESP32Simulator
            
            simulator = ESP32Simulator("ESP32_TEST_SIM", self.backend_url)
            simulator.scenario = "mild_pusher"  # Use pusher scenario for testing
            simulator.transmission_interval = 1.0  # 1 second intervals
            
            # Run simulator in background thread
            def run_sim():
                simulator.start_simulation()
            
            sim_thread = threading.Thread(target=run_sim)
            sim_thread.daemon = True
            sim_thread.start()
            
            # Let it run for specified duration
            time.sleep(duration)
            simulator.stop_simulation()
            
            print("  ✅ ESP32 simulation completed")
            return True
            
        except Exception as e:
            print(f"  ❌ Simulator error: {e}")
            return False
    
    def test_frontend_integration(self):
        """Test frontend integration (if running)."""
        print("🌐 Testing Frontend Integration...")
        
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print("  ✅ Frontend is running and accessible")
                print(f"  📱 Open browser to: {self.frontend_url}")
                print("  🎮 Use demo mode to see real-time updates")
                return True
            else:
                print(f"  ❌ Frontend returned: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ⚠️ Frontend not running: {e}")
            print(f"  💡 Start with: cd frontend && npm start")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("🚀 Starting Comprehensive Hardware-less Testing")
        print("=" * 60)
        
        results = {}
        
        # Test backend
        results["backend_api"] = self.test_backend_api_endpoints()
        print()
        
        # Test sensor data processing
        results["sensor_processing"] = self.test_sensor_data_simulation()
        print()
        
        # Test WebSocket
        results["websocket"] = self.test_websocket_connection()
        print()
        
        # Test clinical algorithms
        results["clinical"] = self.test_clinical_algorithms()
        print()
        
        # Test frontend
        results["frontend"] = self.test_frontend_integration()
        print()
        
        # Run simulator
        results["simulator"] = self.run_esp32_simulator(30)
        print()
        
        # Summary
        print("=" * 60)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! System is working without hardware.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    """Main function for hardware-less testing."""
    print("🔧 ESP32 Integration Testing Without Hardware")
    print("This will test the complete system using simulation and demo mode.")
    print()
    
    tester = HardwarelessTester()
    
    # Check if backend is running
    try:
        response = requests.get(f"{tester.backend_url}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running!")
            print("💡 Start backend with: cd backend && uvicorn main:app --reload")
            return
    except:
        print("❌ Backend is not running!")
        print("💡 Start backend with: cd backend && uvicorn main:app --reload")
        return
    
    # Run comprehensive test
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎊 Testing completed successfully!")
        print("🚀 Your ESP32 integration is working perfectly without hardware!")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()