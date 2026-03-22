/*
=========================================================
Test Configuration Header for ESP32 WiFi Client Tests
Feature: vertex-data-integration, Property 1: ESP32 WiFi Client Reliability

This header file contains configuration constants and test utilities
for the ESP32 WiFi client reliability property tests.

Include this file in your test sketches to access common test
configurations and helper functions.
=========================================================
*/

#ifndef TEST_CONFIG_H
#define TEST_CONFIG_H

#include <WiFi.h>
#include <IPAddress.h>

// === Test Network Configuration ===
// Update these values for your test environment
#define TEST_SSID_PRIMARY "YOUR_PRIMARY_WIFI_SSID"
#define TEST_PASSWORD_PRIMARY "YOUR_PRIMARY_WIFI_PASSWORD"
#define TEST_SSID_SECONDARY "YOUR_SECONDARY_WIFI_SSID"
#define TEST_PASSWORD_SECONDARY "YOUR_SECONDARY_WIFI_PASSWORD"

// Invalid credentials for failure testing
#define TEST_SSID_INVALID "NONEXISTENT_NETWORK_12345"
#define TEST_PASSWORD_INVALID "WRONG_PASSWORD_12345"

// === Test Timing Constants ===
#define TEST_DHCP_TIMEOUT_MS 10000        // 10 seconds for DHCP assignment
#define TEST_RECONNECT_TIMEOUT_MS 10000   // 10 seconds for reconnection
#define TEST_STABILITY_CHECK_INTERVAL_MS 1000  // 1 second between stability checks
#define TEST_POWER_CYCLE_DELAY_MS 2000    // 2 seconds to simulate power cycle
#define TEST_NETWORK_INTERRUPTION_MS 1000 // 1 second network interruption

// === Test Retry Configuration ===
#define TEST_MAX_RECONNECT_ATTEMPTS 3
#define TEST_BASE_RETRY_INTERVAL_MS 1000  // Reduced from 30s for testing
#define TEST_MAX_RETRY_INTERVAL_MS 5000   // Reduced from 300s for testing

// === Test Validation Thresholds ===
#define TEST_MIN_SIGNAL_STRENGTH_DBM -80  // Minimum acceptable signal strength
#define TEST_STABILITY_THRESHOLD_PERCENT 80  // Minimum connection stability percentage
#define TEST_CONNECTION_QUALITY_SAMPLES 10   // Number of samples for quality assessment

// === Backend Server Configuration ===
#define TEST_BACKEND_SERVER_IP "192.168.1.100"  // Update with your backend IP
#define TEST_BACKEND_SERVER_PORT 8000
#define TEST_SENSOR_DATA_ENDPOINT "/api/sensor-data"
#define TEST_CALIBRATION_ENDPOINT "/api/calibration/complete"

// === Test Data Generation ===
#define TEST_DEVICE_ID_PREFIX "TEST_ESP32_"
#define TEST_SESSION_ID_PREFIX "TEST_SESSION_"

// === Test Result Codes ===
typedef enum {
    TEST_RESULT_PASS = 0,
    TEST_RESULT_FAIL = 1,
    TEST_RESULT_TIMEOUT = 2,
    TEST_RESULT_NETWORK_ERROR = 3,
    TEST_RESULT_CONFIG_ERROR = 4
} test_result_t;

// === Test Utility Structures ===
struct TestNetworkConfig {
    const char* ssid;
    const char* password;
    bool shouldConnect;
    const char* description;
};

struct TestConnectionMetrics {
    unsigned long connectionTime;
    IPAddress assignedIP;
    int signalStrength;
    bool dhcpSuccess;
    unsigned long timestamp;
};

struct TestStabilityMetrics {
    int totalChecks;
    int successfulChecks;
    float stabilityPercentage;
    int minSignalStrength;
    int maxSignalStrength;
    unsigned long testDuration;
};

// === Test Utility Functions ===

/**
 * Validate IP address format and range
 * @param ip IP address to validate
 * @return true if valid, false otherwise
 */
inline bool isValidTestIP(IPAddress ip) {
    // Check for invalid addresses
    if (ip == IPAddress(0, 0, 0, 0) || ip == IPAddress(255, 255, 255, 255)) {
        return false;
    }
    
    // Check for private network ranges (typical for test environments)
    uint32_t addr = (uint32_t)ip;
    
    // 192.168.x.x
    if ((addr & 0xFFFF0000) == 0xC0A80000) return true;
    // 10.x.x.x
    if ((addr & 0xFF000000) == 0x0A000000) return true;
    // 172.16.x.x - 172.31.x.x
    if ((addr & 0xFFF00000) == 0xAC100000) return true;
    
    return false;
}

/**
 * Calculate exponential backoff interval
 * @param attempt Attempt number (0-based)
 * @param baseInterval Base interval in milliseconds
 * @param maxInterval Maximum interval in milliseconds
 * @return Calculated interval in milliseconds
 */
inline unsigned long calculateBackoffInterval(int attempt, unsigned long baseInterval, unsigned long maxInterval) {
    unsigned long interval = baseInterval;
    
    // Apply exponential backoff: interval = base * 2^attempt
    for (int i = 0; i < attempt && interval < maxInterval; i++) {
        interval *= 2;
        if (interval > maxInterval) {
            interval = maxInterval;
            break;
        }
    }
    
    return interval;
}

/**
 * Generate test device ID
 * @param buffer Buffer to store device ID
 * @param bufferSize Size of buffer
 */
inline void generateTestDeviceID(char* buffer, size_t bufferSize) {
    uint64_t chipId = ESP.getEfuseMac();
    snprintf(buffer, bufferSize, "%s%04X", TEST_DEVICE_ID_PREFIX, (uint16_t)(chipId & 0xFFFF));
}

/**
 * Print test header with property information
 * @param propertyName Name of the property being tested
 * @param requirements Requirements being validated
 */
inline void printTestHeader(const char* propertyName, const char* requirements) {
    Serial.println("=========================================================");
    Serial.print("Property Test: ");
    Serial.println(propertyName);
    Serial.println("Feature: vertex-data-integration, Property 1");
    Serial.print("Validates Requirements: ");
    Serial.println(requirements);
    Serial.println("=========================================================");
}

/**
 * Print test result summary
 * @param testName Name of the test
 * @param result Test result code
 * @param metrics Optional metrics structure
 */
inline void printTestResult(const char* testName, test_result_t result, const TestConnectionMetrics* metrics = nullptr) {
    Serial.print("Test: ");
    Serial.print(testName);
    Serial.print(" - ");
    
    switch (result) {
        case TEST_RESULT_PASS:
            Serial.println("PASS ✓");
            break;
        case TEST_RESULT_FAIL:
            Serial.println("FAIL ✗");
            break;
        case TEST_RESULT_TIMEOUT:
            Serial.println("TIMEOUT ⏱");
            break;
        case TEST_RESULT_NETWORK_ERROR:
            Serial.println("NETWORK ERROR 🌐");
            break;
        case TEST_RESULT_CONFIG_ERROR:
            Serial.println("CONFIG ERROR ⚙");
            break;
    }
    
    if (metrics && result == TEST_RESULT_PASS) {
        Serial.print("  Connection Time: ");
        Serial.print(metrics->connectionTime);
        Serial.println("ms");
        Serial.print("  Assigned IP: ");
        Serial.println(metrics->assignedIP);
        Serial.print("  Signal Strength: ");
        Serial.print(metrics->signalStrength);
        Serial.println(" dBm");
    }
}

/**
 * Validate test configuration
 * @return true if configuration is valid, false otherwise
 */
inline bool validateTestConfiguration() {
    // Check if test credentials are configured
    if (strcmp(TEST_SSID_PRIMARY, "YOUR_PRIMARY_WIFI_SSID") == 0) {
        Serial.println("ERROR: Test WiFi credentials not configured!");
        Serial.println("Please update TEST_SSID_PRIMARY and TEST_PASSWORD_PRIMARY in test_config.h");
        return false;
    }
    
    // Check timing constants are reasonable
    if (TEST_DHCP_TIMEOUT_MS < 1000 || TEST_DHCP_TIMEOUT_MS > 30000) {
        Serial.println("ERROR: DHCP timeout out of reasonable range (1-30 seconds)");
        return false;
    }
    
    if (TEST_RECONNECT_TIMEOUT_MS < 1000 || TEST_RECONNECT_TIMEOUT_MS > 30000) {
        Serial.println("ERROR: Reconnect timeout out of reasonable range (1-30 seconds)");
        return false;
    }
    
    return true;
}

// === Test Scenario Definitions ===

// Standard test scenarios for property validation
const TestNetworkConfig TEST_SCENARIOS[] = {
    {TEST_SSID_PRIMARY, TEST_PASSWORD_PRIMARY, true, "Primary network (valid credentials)"},
    {TEST_SSID_SECONDARY, TEST_PASSWORD_SECONDARY, true, "Secondary network (valid credentials)"},
    {TEST_SSID_INVALID, TEST_PASSWORD_PRIMARY, false, "Invalid SSID"},
    {TEST_SSID_PRIMARY, TEST_PASSWORD_INVALID, false, "Invalid password"},
    {"", "", false, "Empty credentials"},
    {TEST_SSID_PRIMARY, "", false, "Empty password"},
    {"", TEST_PASSWORD_PRIMARY, false, "Empty SSID"}
};

const int NUM_TEST_SCENARIOS = sizeof(TEST_SCENARIOS) / sizeof(TEST_SCENARIOS[0]);

#endif // TEST_CONFIG_H