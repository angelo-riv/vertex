# ESP32 Property-Based Tests for Vertex Data Integration

This directory contains property-based tests for the ESP32 WiFi client functionality and data transmission completeness as part of the Vertex Data Integration system.

## Overview

**Property 1: ESP32 WiFi Client Reliability**
*For any* ESP32 device with valid network credentials, connecting to WiFi should result in successful DHCP IP assignment, automatic reconnection after power cycles, and recovery within 10 seconds when connectivity is restored.

**Validates Requirements:** 1.2, 1.3, 1.4, 1.5, 1.6, 1.7

**Property 2: ESP32 Data Transmission Completeness**
*For any* sensor reading from ESP32 device, the transmitted JSON should include deviceId, timestamp, pitch angle (±180° with 0.1° precision), FSR values (0-4095 range), pusher detection status, and confidence level, with transmission intervals between 100-200ms and retry logic for failed requests.

**Validates Requirements:** 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7

## Test Structure

### Property Tests Included

#### Property 1: WiFi Client Reliability
1. **DHCP IP Assignment** - Validates that valid credentials result in successful DHCP IP assignment
2. **Credential Persistence** - Tests that WiFi credentials are remembered across power cycles
3. **Reconnection Timing** - Verifies recovery occurs within 10 seconds after connectivity restoration
4. **Exponential Backoff** - Ensures retry intervals increase exponentially with maximum limits
5. **Network Discovery** - Tests ability to discover and communicate with backend services
6. **Connection Stability** - Validates connection remains stable under normal conditions

#### Property 2: Data Transmission Completeness
1. **Data Completeness** - Validates all required JSON fields are present and correctly typed
2. **Pitch Precision** - Tests 0.1 degree precision for pitch angles in ±180° range
3. **FSR Range Validation** - Ensures FSR values are integers in 0-4095 range
4. **Pusher Detection Fields** - Validates boolean status and 0.0-1.0 confidence level
5. **Device Identification** - Tests ESP32_XXXX device ID format and timestamp validity
6. **Transmission Timing** - Verifies 100-200ms transmission intervals
7. **JSON Formatting** - Validates JSON structure and Content-Type headers
8. **Retry Logic** - Tests exponential backoff retry up to 3 attempts

### Test Framework

- **Arduino Unit Testing**: Uses ArduinoUnit library for structured test execution
- **Property-Based Approach**: Tests universal properties across different network scenarios
- **Automated Execution**: Tests run automatically when uploaded to ESP32 device
- **Serial Output**: Results displayed via Serial Monitor at 115200 baud

## Setup Instructions

### Prerequisites

1. **Arduino IDE** with ESP32 board support
2. **Required Libraries** (install via Tools → Manage Libraries):
   - WiFi (ESP32 built-in)
   - ArduinoUnit

### Configuration

1. Open `test_wifi_client_reliability.ino`
2. Update test WiFi credentials:
   ```cpp
   const char* TEST_SSID_VALID = "YOUR_ACTUAL_WIFI_SSID";
   const char* TEST_PASSWORD_VALID = "YOUR_ACTUAL_WIFI_PASSWORD";
   ```

### Running Tests

1. **Arduino IDE Settings:**
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → Select your COM port
   - Serial Monitor Baud Rate → 115200

2. **Upload and Run:**
   - Upload the test sketch to ESP32 device
   - Open Serial Monitor
   - Tests will execute automatically and display results

### Expected Output

```
=========================================================
ESP32 WiFi Client Reliability Property Tests
Feature: vertex-data-integration, Property 1
=========================================================

Test WiFi SSID: YourNetworkName
Starting property-based tests...

=== Testing DHCP IP Assignment Property ===
Testing scenario: Valid credentials
  ✓ DHCP assigned IP: 192.168.1.123
  ✓ Connection time: 3245ms
Testing scenario: Invalid SSID
  ✓ Connection correctly failed for invalid credentials

=== Testing Credential Persistence Property ===
  ✓ Initial connection established
Simulating power cycle...
  ✓ Auto-reconnection successful in 4567ms
  ✓ New IP assigned: 192.168.1.124

=== Testing Reconnection Timing Property ===
  ✓ Initial connection established
Simulating network interruption...
  Reconnection attempt #1
  ✓ Recovery successful in 5432ms
  ✓ Reconnection attempts: 1
  ✓ Signal strength after recovery: -45 dBm

Test summary: 6 passed, 0 failed, 0 skipped
```

## Test Scenarios

### Network Conditions Tested

- **Valid Credentials**: Correct SSID and password
- **Invalid SSID**: Non-existent network name
- **Invalid Password**: Wrong password for existing network
- **Empty Credentials**: Blank SSID and password
- **Network Interruption**: Temporary connectivity loss
- **Power Cycle Simulation**: Device restart scenarios

### Timing Requirements Validated

- **DHCP Assignment**: ≤ 10 seconds
- **Reconnection Recovery**: ≤ 10 seconds
- **Exponential Backoff**: 30s base, max 5 minutes
- **Connection Stability**: 80% uptime over test period

## Integration with Main Firmware

These property tests validate the WiFi functionality that is implemented in the main `Vertex_WiFi_Client.ino` firmware. The tests ensure that the WiFi management functions meet the reliability requirements specified in the design document.

### Key Functions Tested

- `connectToWiFi()` - Initial connection establishment
- `handleWiFiReconnection()` - Automatic reconnection logic
- `isWiFiConnected()` - Connection status validation
- DHCP IP assignment and network discovery
- Credential persistence across power cycles

## Troubleshooting

### Common Issues

1. **Test Configuration Error**
   - Ensure WiFi credentials are properly configured
   - Verify network is accessible from test location

2. **Connection Timeouts**
   - Check WiFi signal strength
   - Verify network allows ESP32 device connections
   - Ensure no MAC address filtering

3. **DHCP Assignment Failures**
   - Verify DHCP server is running on network
   - Check for IP address pool exhaustion
   - Ensure no static IP conflicts

### Debug Information

The tests provide detailed debug output including:
- Connection timing measurements
- IP address assignments
- Signal strength readings
- Retry attempt counts
- Error conditions and recovery

## Clinical Validation

These property tests ensure the ESP32 WiFi client meets the reliability requirements for clinical use:

- **Consistent Connectivity**: Reliable connection for real-time patient monitoring
- **Automatic Recovery**: Minimal disruption during network interruptions
- **Predictable Behavior**: Deterministic reconnection patterns for clinical environments
- **Performance Validation**: Sub-10-second recovery times for continuous monitoring

The property-based approach validates these requirements across diverse network conditions and failure scenarios, ensuring robust performance in clinical settings.