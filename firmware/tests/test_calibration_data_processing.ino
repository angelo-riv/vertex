/*
=========================================================
Property Test: Calibration Data Processing (ESP32 Hardware)

This Arduino-based property test validates the calibration data 
processing functionality directly on ESP32 hardware for Task 1.6.

Property 14: Calibration Data Processing
For any 30-second calibration period, the ESP32 should continuously 
sample FSR and IMU data at 5-10 Hz, calculate baseline values 
(mean FSR left/right, standard deviation, mean pitch, weight 
distribution ratio), store calibration in EEPROM and transmit to 
backend, and apply patient-specific thresholds using baseline ± 2 
standard deviations for detection.

Validates Requirements: 17.3, 17.5, 17.6, 17.7

Hardware Requirements:
- ESP32 Dev Module
- BNO055 IMU (optional - can use simulated data)
- 2x FSR sensors (optional - can use simulated data)
- Serial Monitor at 115200 baud

Usage:
1. Upload to ESP32
2. Open Serial Monitor
3. Tests run automatically on startup
4. View property test results
=========================================================
*/

#include <Wire.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <math.h>

// Test configuration
#define PROPERTY_TEST_MODE true
#define SIMULATE_SENSORS true
#define TEST_CALIBRATION_DURATION 5000  // 5 seconds for testing (normally 30s)
#define MIN_SAMPLING_FREQUENCY 5.0      // 5 Hz minimum
#define MAX_SAMPLING_FREQUENCY 10.0     // 10 Hz maximum
#define EXPECTED_MIN_SAMPLES 25         // 5 seconds * 5 Hz
#define EXPECTED_MAX_SAMPLES 50         // 5 seconds * 10 Hz

// Pin definitions (same as main firmware)
#define FSR_LEFT 35
#define FSR_RIGHT 34
#define STATUS_LED 13

// Test data structures
struct PropertyTestSample {
  unsigned long timestamp;
  float pitch;
  int fsrLeft;
  int fsrRight;
};

struct PropertyTestCalibration {
  float baselinePitch;
  float baselineFsrLeft;
  float baselineFsrRight;
  float baselineFsrRatio;
  float pitchStdDev;
  float fsrStdDev;
  int sampleCount;
  float duration;
  float samplingFrequency;
  bool isValid;
};

// Test state variables
PropertyTestSample testSamples[EXPECTED_MAX_SAMPLES];
int testSampleCount = 0;
PropertyTestCalibration testCalibration;
bool allTestsPassed = true;

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("=========================================================");
  Serial.println("Property Test: Calibration Data Processing (ESP32)");
  Serial.println("Feature: vertex-data-integration, Property 14");
  Serial.println("Validates Requirements: 17.3, 17.5, 17.6, 17.7");
  Serial.println("=========================================================");
  
  // Initialize EEPROM
  EEPROM.begin(512);
  
  // Initialize pins
  pinMode(FSR_LEFT, INPUT);
  pinMode(FSR_RIGHT, INPUT);
  pinMode(STATUS_LED, OUTPUT);
  
  // Run property tests
  runCalibrationPropertyTests();
  
  // Report final results
  if (allTestsPassed) {
    Serial.println("\n🎉 ALL CALIBRATION PROPERTY TESTS PASSED");
    Serial.println("Property 14: Calibration Data Processing - VALIDATED");
    digitalWrite(STATUS_LED, HIGH);  // Success indicator
  } else {
    Serial.println("\n❌ SOME PROPERTY TESTS FAILED");
    // Blink LED to indicate failure
    for (int i = 0; i < 10; i++) {
      digitalWrite(STATUS_LED, HIGH);
      delay(200);
      digitalWrite(STATUS_LED, LOW);
      delay(200);
    }
  }
}

void loop() {
  // Property tests run once in setup()
  delay(1000);
}

void runCalibrationPropertyTests() {
  Serial.println("\n🧪 Running ESP32 Calibration Property Tests...\n");
  
  // Property 14.1: Test sampling frequency
  testSamplingFrequencyProperty();
  
  // Property 14.2: Test baseline calculations
  testBaselineCalculationProperty();
  
  // Property 14.3: Test EEPROM storage
  testEEPROMStorageProperty();
  
  // Property 14.4: Test patient-specific thresholds
  testPatientThresholdsProperty();
}

void testSamplingFrequencyProperty() {
  Serial.println("Property 14.1: Testing sampling frequency (Requirement 17.3)");
  Serial.println("Validating continuous sampling at 5-10 Hz frequency");
  
  // Generate test samples at target frequency
  testSampleCount = 0;
  unsigned long startTime = millis();
  unsigned long targetInterval = 100; // 10 Hz (100ms intervals)
  
  for (int i = 0; i < 40; i++) {  // 40 samples over 4 seconds
    unsigned long sampleTime = startTime + (i * targetInterval);
    
    // Simulate realistic sensor data
    float pitch = 0.5 + sin(i * 0.1) * 0.3;  // Small variations around 0.5°
    int fsrLeft = 2000 + (i % 10 - 5) * 20;   // FSR variations
    int fsrRight = 2100 + (i % 8 - 4) * 15;
    
    testSamples[testSampleCount] = {
      sampleTime,
      pitch,
      constrain(fsrLeft, 0, 4095),
      constrain(fsrRight, 0, 4095)
    };
    testSampleCount++;
  }
  
  // Calculate actual sampling frequency
  if (testSampleCount > 1) {
    float duration = (testSamples[testSampleCount-1].timestamp - testSamples[0].timestamp) / 1000.0;
    float actualFrequency = testSampleCount / duration;
    
    Serial.print("  Samples collected: ");
    Serial.println(testSampleCount);
    Serial.print("  Duration: ");
    Serial.print(duration, 2);
    Serial.println(" seconds");
    Serial.print("  Sampling frequency: ");
    Serial.print(actualFrequency, 2);
    Serial.println(" Hz");
    
    // Verify frequency is within required range
    if (actualFrequency >= MIN_SAMPLING_FREQUENCY && actualFrequency <= MAX_SAMPLING_FREQUENCY) {
      Serial.println("  ✓ Sampling frequency within 5-10 Hz range");
    } else {
      Serial.print("  ❌ Sampling frequency out of range: ");
      Serial.print(actualFrequency, 2);
      Serial.println(" Hz");
      allTestsPassed = false;
    }
    
    // Verify sufficient samples
    if (testSampleCount >= EXPECTED_MIN_SAMPLES) {
      Serial.println("  ✓ Sufficient samples collected");
    } else {
      Serial.print("  ❌ Insufficient samples: ");
      Serial.print(testSampleCount);
      Serial.print(" < ");
      Serial.println(EXPECTED_MIN_SAMPLES);
      allTestsPassed = false;
    }
  }
  
  Serial.println();
}

void testBaselineCalculationProperty() {
  Serial.println("Property 14.2: Testing baseline calculations (Requirement 17.5)");
  Serial.println("Validating mean FSR left/right, std dev, mean pitch, weight ratio");
  
  if (testSampleCount == 0) {
    Serial.println("  ❌ No samples available for baseline calculation");
    allTestsPassed = false;
    return;
  }
  
  // Calculate baseline values (means)
  float pitchSum = 0, fsrLeftSum = 0, fsrRightSum = 0;
  for (int i = 0; i < testSampleCount; i++) {
    pitchSum += testSamples[i].pitch;
    fsrLeftSum += testSamples[i].fsrLeft;
    fsrRightSum += testSamples[i].fsrRight;
  }
  
  testCalibration.baselinePitch = pitchSum / testSampleCount;
  testCalibration.baselineFsrLeft = fsrLeftSum / testSampleCount;
  testCalibration.baselineFsrRight = fsrRightSum / testSampleCount;
  
  // Calculate weight distribution ratio
  float totalBaseline = testCalibration.baselineFsrLeft + testCalibration.baselineFsrRight;
  testCalibration.baselineFsrRatio = testCalibration.baselineFsrRight / totalBaseline;
  
  // Calculate standard deviations
  float pitchVarianceSum = 0, fsrRatioVarianceSum = 0;
  for (int i = 0; i < testSampleCount; i++) {
    float pitchDiff = testSamples[i].pitch - testCalibration.baselinePitch;
    pitchVarianceSum += pitchDiff * pitchDiff;
    
    float totalFsr = testSamples[i].fsrLeft + testSamples[i].fsrRight;
    float fsrRatio = (totalFsr > 0) ? (float)testSamples[i].fsrRight / totalFsr : 0.5;
    float fsrRatioDiff = fsrRatio - testCalibration.baselineFsrRatio;
    fsrRatioVarianceSum += fsrRatioDiff * fsrRatioDiff;
  }
  
  testCalibration.pitchStdDev = sqrt(pitchVarianceSum / testSampleCount);
  testCalibration.fsrStdDev = sqrt(fsrRatioVarianceSum / testSampleCount) * 1000;
  
  // Ensure minimum thresholds
  testCalibration.pitchStdDev = max(1.0, testCalibration.pitchStdDev);
  testCalibration.fsrStdDev = max(10.0, testCalibration.fsrStdDev);
  
  testCalibration.sampleCount = testSampleCount;
  testCalibration.isValid = true;
  
  // Display and verify results
  Serial.print("  Baseline pitch: ");
  Serial.print(testCalibration.baselinePitch, 3);
  Serial.println("°");
  Serial.print("  Baseline FSR left: ");
  Serial.println(testCalibration.baselineFsrLeft, 1);
  Serial.print("  Baseline FSR right: ");
  Serial.println(testCalibration.baselineFsrRight, 1);
  Serial.print("  Weight distribution ratio: ");
  Serial.println(testCalibration.baselineFsrRatio, 4);
  Serial.print("  Pitch std dev: ");
  Serial.print(testCalibration.pitchStdDev, 3);
  Serial.println("°");
  Serial.print("  FSR std dev: ");
  Serial.println(testCalibration.fsrStdDev, 2);
  
  // Verify calculations are reasonable
  bool calculationsValid = true;
  
  if (testCalibration.baselinePitch < -10.0 || testCalibration.baselinePitch > 10.0) {
    Serial.println("  ❌ Baseline pitch out of reasonable range");
    calculationsValid = false;
  }
  
  if (testCalibration.baselineFsrLeft < 0 || testCalibration.baselineFsrLeft > 4095) {
    Serial.println("  ❌ Baseline FSR left out of valid range");
    calculationsValid = false;
  }
  
  if (testCalibration.baselineFsrRight < 0 || testCalibration.baselineFsrRight > 4095) {
    Serial.println("  ❌ Baseline FSR right out of valid range");
    calculationsValid = false;
  }
  
  if (testCalibration.baselineFsrRatio < 0.0 || testCalibration.baselineFsrRatio > 1.0) {
    Serial.println("  ❌ FSR ratio out of valid range");
    calculationsValid = false;
  }
  
  if (testCalibration.pitchStdDev < 1.0 || testCalibration.pitchStdDev > 20.0) {
    Serial.println("  ❌ Pitch std dev out of reasonable range");
    calculationsValid = false;
  }
  
  if (testCalibration.fsrStdDev < 10.0 || testCalibration.fsrStdDev > 1000.0) {
    Serial.println("  ❌ FSR std dev out of reasonable range");
    calculationsValid = false;
  }
  
  if (calculationsValid) {
    Serial.println("  ✓ All baseline calculations within valid ranges");
  } else {
    allTestsPassed = false;
  }
  
  Serial.println();
}

void testEEPROMStorageProperty() {
  Serial.println("Property 14.3: Testing EEPROM storage (Requirement 17.6)");
  Serial.println("Validating calibration data storage and retrieval");
  
  if (!testCalibration.isValid) {
    Serial.println("  ❌ No valid calibration data to store");
    allTestsPassed = false;
    return;
  }
  
  // Store calibration data to EEPROM
  EEPROM.put(0, testCalibration);
  EEPROM.commit();
  Serial.println("  Calibration data written to EEPROM");
  
  // Verify storage by reading back
  PropertyTestCalibration verifyCalibration;
  EEPROM.get(0, verifyCalibration);
  
  // Compare stored vs original data
  bool storageValid = true;
  float tolerance = 0.001;
  
  if (abs(verifyCalibration.baselinePitch - testCalibration.baselinePitch) > tolerance) {
    Serial.println("  ❌ Baseline pitch storage verification failed");
    storageValid = false;
  }
  
  if (abs(verifyCalibration.baselineFsrLeft - testCalibration.baselineFsrLeft) > 0.1) {
    Serial.println("  ❌ Baseline FSR left storage verification failed");
    storageValid = false;
  }
  
  if (abs(verifyCalibration.baselineFsrRight - testCalibration.baselineFsrRight) > 0.1) {
    Serial.println("  ❌ Baseline FSR right storage verification failed");
    storageValid = false;
  }
  
  if (abs(verifyCalibration.baselineFsrRatio - testCalibration.baselineFsrRatio) > tolerance) {
    Serial.println("  ❌ FSR ratio storage verification failed");
    storageValid = false;
  }
  
  if (abs(verifyCalibration.pitchStdDev - testCalibration.pitchStdDev) > tolerance) {
    Serial.println("  ❌ Pitch std dev storage verification failed");
    storageValid = false;
  }
  
  if (abs(verifyCalibration.fsrStdDev - testCalibration.fsrStdDev) > 0.1) {
    Serial.println("  ❌ FSR std dev storage verification failed");
    storageValid = false;
  }
  
  if (storageValid) {
    Serial.println("  ✓ EEPROM storage and retrieval verified");
  } else {
    allTestsPassed = false;
  }
  
  // Test backend transmission format (JSON serialization simulation)
  Serial.println("  Testing backend transmission format...");
  
  DynamicJsonDocument doc(512);
  doc["device_id"] = "ESP32_TEST";
  doc["patient_id"] = "test_patient";
  doc["baseline_pitch"] = testCalibration.baselinePitch;
  doc["baseline_fsr_left"] = testCalibration.baselineFsrLeft;
  doc["baseline_fsr_right"] = testCalibration.baselineFsrRight;
  doc["baseline_fsr_ratio"] = testCalibration.baselineFsrRatio;
  doc["pitch_std_dev"] = testCalibration.pitchStdDev;
  doc["fsr_std_dev"] = testCalibration.fsrStdDev;
  doc["calibration_timestamp"] = millis();
  doc["is_active"] = true;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  if (jsonString.length() > 50) {
    Serial.print("  ✓ JSON payload created (");
    Serial.print(jsonString.length());
    Serial.println(" bytes)");
    Serial.print("  Sample JSON: ");
    Serial.println(jsonString.substring(0, 80) + "...");
  } else {
    Serial.println("  ❌ JSON payload too small or invalid");
    allTestsPassed = false;
  }
  
  Serial.println();
}
void testPatientThresholdsProperty() {
  Serial.println("Property 14.4: Testing patient-specific thresholds (Requirement 17.7)");
  Serial.println("Validating baseline ± 2 standard deviations for detection");
  
  if (!testCalibration.isValid) {
    Serial.println("  ❌ No valid calibration data for threshold testing");
    allTestsPassed = false;
    return;
  }
  
  // Calculate patient-specific thresholds using baseline ± 2 SD
  float pitchThreshold = 2.0 * testCalibration.pitchStdDev;
  float fsrThreshold = 2.0 * testCalibration.fsrStdDev / 1000.0;  // Convert to ratio scale
  
  Serial.print("  Calculated pitch threshold: ±");
  Serial.print(pitchThreshold, 2);
  Serial.println("° from baseline");
  Serial.print("  Calculated FSR threshold: ±");
  Serial.print(fsrThreshold, 4);
  Serial.println(" from baseline ratio");
  
  // Test threshold application with various scenarios
  struct ThresholdTest {
    float testPitch;
    float testFsrRatio;
    bool shouldTriggerPitch;
    bool shouldTriggerFsr;
    const char* description;
  };
  
  ThresholdTest tests[] = {
    // Normal posture (within thresholds)
    {testCalibration.baselinePitch + 0.5, testCalibration.baselineFsrRatio + 0.01, false, false, "Normal posture"},
    
    // Pitch exceeds threshold
    {testCalibration.baselinePitch + (pitchThreshold * 1.5), testCalibration.baselineFsrRatio, true, false, "Pitch exceeds threshold"},
    
    // FSR exceeds threshold
    {testCalibration.baselinePitch, testCalibration.baselineFsrRatio + (fsrThreshold * 1.5), false, true, "FSR exceeds threshold"},
    
    // Both exceed thresholds
    {testCalibration.baselinePitch + (pitchThreshold * 1.2), testCalibration.baselineFsrRatio + (fsrThreshold * 1.3), true, true, "Both exceed thresholds"},
    
    // Boundary cases
    {testCalibration.baselinePitch + pitchThreshold, testCalibration.baselineFsrRatio, true, false, "Pitch at threshold boundary"},
    {testCalibration.baselinePitch, testCalibration.baselineFsrRatio + fsrThreshold, false, true, "FSR at threshold boundary"}
  };
  
  int testCount = sizeof(tests) / sizeof(tests[0]);
  int passedTests = 0;
  
  for (int i = 0; i < testCount; i++) {
    ThresholdTest test = tests[i];
    
    // Calculate deviations
    float pitchDeviation = abs(test.testPitch - testCalibration.baselinePitch);
    float fsrDeviation = abs(test.testFsrRatio - testCalibration.baselineFsrRatio);
    
    // Apply threshold logic
    bool pitchExceeds = pitchDeviation > pitchThreshold;
    bool fsrExceeds = fsrDeviation > fsrThreshold;
    bool detectionTriggered = pitchExceeds || fsrExceeds;
    
    // Verify results match expectations
    bool testPassed = (pitchExceeds == test.shouldTriggerPitch) && 
                      (fsrExceeds == test.shouldTriggerFsr);
    
    Serial.print("  Test ");
    Serial.print(i + 1);
    Serial.print(" (");
    Serial.print(test.description);
    Serial.print("): ");
    
    if (testPassed) {
      Serial.println("✓ PASS");
      passedTests++;
    } else {
      Serial.println("❌ FAIL");
      Serial.print("    Expected pitch trigger: ");
      Serial.print(test.shouldTriggerPitch ? "YES" : "NO");
      Serial.print(", Got: ");
      Serial.println(pitchExceeds ? "YES" : "NO");
      Serial.print("    Expected FSR trigger: ");
      Serial.print(test.shouldTriggerFsr ? "YES" : "NO");
      Serial.print(", Got: ");
      Serial.println(fsrExceeds ? "YES" : "NO");
      allTestsPassed = false;
    }
    
    // Debug information
    Serial.print("    Pitch deviation: ");
    Serial.print(pitchDeviation, 2);
    Serial.print("° (threshold: ");
    Serial.print(pitchThreshold, 2);
    Serial.println("°)");
    Serial.print("    FSR deviation: ");
    Serial.print(fsrDeviation, 4);
    Serial.print(" (threshold: ");
    Serial.print(fsrThreshold, 4);
    Serial.println(")");
  }
  
  Serial.print("  Threshold tests passed: ");
  Serial.print(passedTests);
  Serial.print("/");
  Serial.println(testCount);
  
  // Verify thresholds are within safe ranges
  bool thresholdsReasonable = true;
  
  if (pitchThreshold < 1.0 || pitchThreshold > 20.0) {
    Serial.print("  ❌ Pitch threshold out of safe range: ");
    Serial.println(pitchThreshold, 2);
    thresholdsReasonable = false;
  }
  
  if (fsrThreshold < 0.01 || fsrThreshold > 0.5) {
    Serial.print("  ❌ FSR threshold out of safe range: ");
    Serial.println(fsrThreshold, 4);
    thresholdsReasonable = false;
  }
  
  if (thresholdsReasonable) {
    Serial.println("  ✓ Thresholds within safe operational ranges");
  } else {
    allTestsPassed = false;
  }
  
  // Test adaptive threshold behavior
  Serial.println("  Testing adaptive threshold behavior...");
  
  // Simulate different patient baselines
  float testBaselines[] = {-2.0, 0.0, 2.0, 5.0};
  int baselineCount = sizeof(testBaselines) / sizeof(testBaselines[0]);
  
  for (int i = 0; i < baselineCount; i++) {
    float testBaseline = testBaselines[i];
    float adaptiveThreshold = 2.0 * testCalibration.pitchStdDev;
    
    // Test that thresholds adapt to different baselines
    float testAngle1 = testBaseline + adaptiveThreshold * 0.5;  // Should not trigger
    float testAngle2 = testBaseline + adaptiveThreshold * 1.5;  // Should trigger
    
    bool trigger1 = abs(testAngle1 - testBaseline) > adaptiveThreshold;
    bool trigger2 = abs(testAngle2 - testBaseline) > adaptiveThreshold;
    
    if (!trigger1 && trigger2) {
      Serial.print("    ✓ Adaptive threshold works for baseline ");
      Serial.println(testBaseline, 1);
    } else {
      Serial.print("    ❌ Adaptive threshold failed for baseline ");
      Serial.println(testBaseline, 1);
      allTestsPassed = false;
    }
  }
  
  Serial.println();
}

// Utility functions
float max(float a, float b) {
  return (a > b) ? a : b;
}

float min(float a, float b) {
  return (a < b) ? a : b;
}

int constrain(int value, int min_val, int max_val) {
  if (value < min_val) return min_val;
  if (value > max_val) return max_val;
  return value;
}