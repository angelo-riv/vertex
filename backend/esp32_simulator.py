# ESP32 Hardware Simulator for Testing
# Simulates ESP32 device behavior without physical hardware

import asyncio
import json
import time
import random
import math
import requests
from datetime import datetime, timezone
import threading

class ESP32Simulator:
    """
    Simulates ESP32 device behavior for testing without physical hardware.
    
    Features:
    - Realistic sensor data generation
    - Various patient scenarios (normal, pusher syndrome, etc.)
    - Calibration simulation
    - Network connectivity simulation
    - Multiple device simulation
    """
    
    def __init__(self, device_id="ESP32_SIM_001", backend_url="http://localhost:8000"):
        self.device_id = device_id
        self.backend_url = backend_url
        self.is_running = False
        self.scenario = "normal"  # normal, mild_pusher, severe_pusher, calibrating
        self.calibration_baseline = None
        self.transmission_interval = 0.2  # 200ms (5 Hz)
        
        # Simulation parameters
        self.base_pitch = 0.0
        self.base_roll = 0.0
        self.base_fsr_left = 2048
        self.base_fsr_right = 2048
        
        # Scenario configurations
        self.scenarios = {
            "normal": {
                "pitch_range": (-3, 3),
                "roll_range": (-2, 2),
                "fsr_imbalance": 0.1,  # 10% max imbalance
                "pusher_probability": 0.0
            },
            "mild_pusher": {
                "pitch_range": (-8, 12),
                "roll_range": (-3, 5),
                "fsr_imbalance": 0.25,  # 25% imbalance
                "pusher_probability": 0.3
            },
            "severe_pusher": {
                "pitch_range": (-5, 25),
                "roll_range": (-2, 8),
                "fsr_imbalance": 0.4,  # 40% imbalance
                "pusher_probability": 0.7
            },
            "calibrating": {
                "pitch_range": (-1, 1),
                "roll_range": (-0.5, 0.5),
                "fsr_imbalance": 0.05,  # Very stable during calibration
                "pusher_probability": 0.0
            }
        }
    
    def generate_sensor_data(self):
        """Generate realistic sensor data based on current scenario."""
        scenario_config = self.scenarios[self.scenario]
        
        # Generate pitch with scenario-specific behavior
        if random.random() < scenario_config["pusher_probability"]:
            # Pusher episode - lean toward affected side
            pitch = random.uniform(10, scenario_config["pitch_range"][1])
        else:
            # Normal variation
            pitch = random.uniform(*scenario_config["pitch_range"])
        
        # Add baseline offset if calibrated
        if self.calibration_baseline:
            pitch += self.calibration_baseline["pitch"]
        
        # Generate roll and yaw
        roll = random.uniform(*scenario_config["roll_range"])
        yaw = random.uniform(-2, 2)
        
        # Generate FSR data with imbalance
        imbalance_factor = scenario_config["fsr_imbalance"]
        imbalance = random.uniform(-imbalance_factor, imbalance_factor)
        
        fsr_left = int(self.base_fsr_left * (1 - imbalance))
        fsr_right = int(self.base_fsr_right * (1 + imbalance))
        
        # Add noise
        fsr_left += random.randint(-20, 20)
        fsr_right += random.randint(-20, 20)
        
        # Ensure valid ranges
        fsr_left = max(0, min(4095, fsr_left))
        fsr_right = max(0, min(4095, fsr_right))
        
        return {
            "deviceId": self.device_id,
            "timestamp": int(time.time() * 1000),
            "pitch": round(pitch, 2),
            "roll": round(roll, 2),
            "yaw": round(yaw, 2),
            "fsrLeft": fsr_left,
            "fsrRight": fsr_right
        }
    
    def send_sensor_data(self, data):
        """Send sensor data to backend API."""
        try:
            headers = {
                "X-Device-ID": self.device_id,
                "X-Device-Signature": "simulated_signature",
                "X-Timestamp": str(int(time.time())),
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/sensor-data",
                json=data,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def simulate_calibration(self, duration=30):
        """Simulate 30-second calibration process."""
        print(f"🎯 Starting {duration}-second calibration simulation...")
        
        self.scenario = "calibrating"
        calibration_data = []
        
        for i in range(duration):
            # Generate stable calibration data
            data = self.generate_sensor_data()
            calibration_data.append(data)
            
            success, result = self.send_sensor_data(data)
            if success:
                print(f"  Calibration progress: {i+1}/{duration} seconds")
            else:
                print(f"  Calibration error: {result}")
            
            time.sleep(1)  # 1 second intervals during calibration
        
        # Calculate baseline from calibration data
        avg_pitch = sum(d["pitch"] for d in calibration_data) / len(calibration_data)
        avg_fsr_left = sum(d["fsrLeft"] for d in calibration_data) / len(calibration_data)
        avg_fsr_right = sum(d["fsrRight"] for d in calibration_data) / len(calibration_data)
        
        self.calibration_baseline = {
            "pitch": avg_pitch,
            "fsrLeft": avg_fsr_left,
            "fsrRight": avg_fsr_right,
            "ratio": avg_fsr_left / avg_fsr_right if avg_fsr_right > 0 else 1.0,
            "stdDev": 0.8  # Simulated standard deviation
        }
        
        print(f"✅ Calibration complete! Baseline: {self.calibration_baseline}")
        return self.calibration_baseline
    
    def start_simulation(self):
        """Start continuous sensor data simulation."""
        print(f"🚀 Starting ESP32 simulation for device {self.device_id}")
        print(f"   Scenario: {self.scenario}")
        print(f"   Interval: {self.transmission_interval}s")
        print(f"   Backend: {self.backend_url}")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Generate and send sensor data
                data = self.generate_sensor_data()
                success, result = self.send_sensor_data(data)
                
                if success:
                    clinical = result.get("clinical_analysis", {})
                    pusher_detected = clinical.get("pusher_detected", False)
                    clinical_score = clinical.get("clinical_score", 0)
                    
                    status = "🔴 PUSHER" if pusher_detected else "🟢 NORMAL"
                    print(f"{status} | Pitch: {data['pitch']:+6.2f}° | FSR: {data['fsrLeft']}/{data['fsrRight']} | Score: {clinical_score}")
                else:
                    print(f"❌ Transmission failed: {result}")
                
                time.sleep(self.transmission_interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ Simulation stopped by user")
                break
            except Exception as e:
                print(f"❌ Simulation error: {e}")
                time.sleep(1)
        
        self.is_running = False
    
    def stop_simulation(self):
        """Stop the simulation."""
        self.is_running = False
    
    def set_scenario(self, scenario):
        """Change simulation scenario."""
        if scenario in self.scenarios:
            self.scenario = scenario
            print(f"📋 Scenario changed to: {scenario}")
        else:
            print(f"❌ Unknown scenario: {scenario}")
            print(f"Available scenarios: {list(self.scenarios.keys())}")

def main():
    """Main function for running ESP32 simulator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ESP32 Hardware Simulator")
    parser.add_argument("--device-id", default="ESP32_SIM_001", help="Device ID")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--scenario", default="normal", choices=["normal", "mild_pusher", "severe_pusher"], help="Simulation scenario")
    parser.add_argument("--interval", type=float, default=0.2, help="Transmission interval in seconds")
    parser.add_argument("--calibrate", action="store_true", help="Run calibration simulation first")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = ESP32Simulator(args.device_id, args.backend_url)
    simulator.scenario = args.scenario
    simulator.transmission_interval = args.interval
    
    try:
        # Run calibration if requested
        if args.calibrate:
            simulator.simulate_calibration()
            print("\nPress Enter to continue with normal simulation...")
            input()
        
        # Start continuous simulation
        simulator.start_simulation()
        
    except KeyboardInterrupt:
        print("\n👋 Simulator stopped")

if __name__ == "__main__":
    main()