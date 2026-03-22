#!/usr/bin/env python3
"""
Simple test for demo mode data generation.
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from demo_data_generator import DemoDataGenerator

def test_basic_generation():
    """Test basic demo data generation"""
    print("Testing Basic Demo Data Generation")
    print("=" * 40)
    
    generator = DemoDataGenerator("ESP32_TEST")
    
    # Test each scenario manually
    scenarios = [
        "normal_posture",
        "mild_pusher_episode", 
        "moderate_pusher_episode",
        "severe_pusher_episode",
        "correction_attempt",
        "recovery_phase"
    ]
    
    print("Testing each scenario:")
    for scenario in scenarios:
        generator.current_scenario = scenario
        generator.target_pitch = generator._get_scenario_target_pitch()
        generator.current_pitch = generator.target_pitch  # Set directly for immediate results
        
        reading = generator.generate_reading()
        pusher_active = generator._is_pusher_episode_active()
        
        print(f"{scenario:25s}: pitch={reading.pitch:6.1f}°, pusher={reading.pusher_detected}, "
              f"expected_pusher={pusher_active}, FSR_L={reading.fsr_left}, FSR_R={reading.fsr_right}")
    
    print("\nTesting pitch range over time:")
    pitch_values = []
    pusher_count = 0
    
    # Force scenario changes to test variety
    for i in range(30):
        if i % 5 == 0:  # Change scenario every 5 readings
            scenario_idx = (i // 5) % len(scenarios)
            generator.current_scenario = scenarios[scenario_idx]
            generator.target_pitch = generator._get_scenario_target_pitch()
            generator.current_pitch = generator.target_pitch  # Direct assignment for testing
        
        reading = generator.generate_reading()
        pitch_values.append(reading.pitch)
        if reading.pusher_detected:
            pusher_count += 1
        
        if i < 10:  # Show first 10 readings
            print(f"Reading {i+1:2d}: {generator.current_scenario:20s} -> pitch={reading.pitch:6.1f}°, pusher={reading.pusher_detected}")
    
    min_pitch = min(pitch_values)
    max_pitch = max(pitch_values)
    pusher_percentage = (pusher_count / 30) * 100
    
    print(f"\nResults:")
    print(f"Pitch range: {min_pitch:.1f}° to {max_pitch:.1f}°")
    print(f"Pusher events: {pusher_count}/30 ({pusher_percentage:.1f}%)")
    
    # Check requirements
    range_ok = -15 <= min_pitch and max_pitch <= 15 and (max_pitch - min_pitch) > 5
    pusher_ok = pusher_count > 0
    
    print(f"\nRequirement checks:")
    print(f"Pitch range variety: {'✓' if range_ok else '✗'}")
    print(f"Pusher events present: {'✓' if pusher_ok else '✗'}")
    
    return range_ok and pusher_ok

if __name__ == "__main__":
    success = test_basic_generation()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)