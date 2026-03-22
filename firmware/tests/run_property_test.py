#!/usr/bin/env python3
"""
Quick validation of ESP32 Data Transmission Completeness Property Test
"""

import time
from test_esp32_data_transmission import ESP32DataTransmissionTester

def main():
    # Test core functionality
    tester = ESP32DataTransmissionTester()

    # Test 1: Data completeness validation
    test_data = {
        'device_id': 'ESP32_ABC123',
        'session_id': None,
        'timestamp': int(time.time() * 1000),  # Use current timestamp
        'pitch': 15.2,
        'roll': -3.1,
        'yaw': 0.0,
        'fsr_left': 1024,
        'fsr_right': 1156,
        'pusher_detected': True,
        'confidence_level': 0.85
    }

    print('=== ESP32 Data Transmission Completeness Property Test ===')
    print('Feature: vertex-data-integration, Property 2')
    print('Validates Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7')
    print()

    # Test data completeness
    completeness_result = tester.validate_data_completeness(test_data)
    print(f'✓ Data completeness validation: {"PASS" if completeness_result else "FAIL"}')

    # Test pitch precision
    pitch_result = tester.validate_pitch_precision(15.2)
    print(f'✓ Pitch precision validation: {"PASS" if pitch_result else "FAIL"}')

    # Test FSR range
    fsr_result = tester.validate_fsr_range(1024, 1156)
    print(f'✓ FSR range validation: {"PASS" if fsr_result else "FAIL"}')

    # Test pusher detection fields
    pusher_result = tester.validate_pusher_detection_fields(True, 0.85)
    print(f'✓ Pusher detection fields validation: {"PASS" if pusher_result else "FAIL"}')

    # Test device identification
    device_result = tester.validate_device_identification('ESP32_ABC123', int(time.time() * 1000))
    print(f'✓ Device identification validation: {"PASS" if device_result else "FAIL"}')

    # Test transmission timing
    timing_result = tester.validate_transmission_timing([0.15, 0.12, 0.18])
    print(f'✓ Transmission timing validation: {"PASS" if timing_result else "FAIL"}')

    # Test edge cases
    print()
    print('=== Edge Case Testing ===')
    
    # Test boundary values
    edge_cases = [
        # Pitch boundaries
        (tester.validate_pitch_precision(-180.0), "Pitch -180.0 degrees"),
        (tester.validate_pitch_precision(180.0), "Pitch +180.0 degrees"),
        (tester.validate_pitch_precision(0.1), "Pitch 0.1 degrees"),
        
        # FSR boundaries
        (tester.validate_fsr_range(0, 4095), "FSR min/max values"),
        (tester.validate_fsr_range(2048, 2048), "FSR equal values"),
        
        # Confidence boundaries
        (tester.validate_pusher_detection_fields(False, 0.0), "Confidence 0.0"),
        (tester.validate_pusher_detection_fields(True, 1.0), "Confidence 1.0"),
    ]
    
    for result, description in edge_cases:
        print(f'✓ {description}: {"PASS" if result else "FAIL"}')

    print()
    all_passed = all([completeness_result, pitch_result, fsr_result, pusher_result, device_result, timing_result])
    if all_passed:
        print('🎉 ALL PROPERTY TESTS PASSED')
        print('ESP32 data transmission completeness validated!')
        return True
    else:
        print('❌ SOME TESTS FAILED')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)