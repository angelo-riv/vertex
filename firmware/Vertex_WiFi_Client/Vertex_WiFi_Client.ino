/*
=========================================================
Vertex WiFi Client Firmware - ESP32 Data Integration

REQUIRED ARDUINO SETTINGS:
--------------------------------
Tools → Board → ESP32 Dev Module
Tools → Port  → Select your COM port
Serial Monitor Baud Rate → 115200

REQUIRED LIBRARIES (Install via Tools → Manage Libraries):
--------------------------------
1. Adafruit Unified Sensor
2. Adafruit BNO055
3. ArduinoJson (for HTTP POST JSON formatting)
4. HTTPClient (ESP32 built-in)

WIRING (BNO055 → ESP32):
--------------------------------
VIN  → 3.3V
GND  → GND
SDA  → GPIO21
SCL  → GPIO22
FSR1 → GPIO34
FSR2 → GPIO35
MOTOR_LEFT → GPIO25
MOTOR_RIGHT → GPIO26
PB2 (Calibration) → GPIO2 (with pull-up resistor)
STATUS_LED → GPIO13

IMPORTANT:
- Configure WiFi credentials in the setup() function
- Backend server IP will be auto-discovered or manually configured
- USB power is sufficient for testing
- Do NOT use 5V to power BNO055 logic
=========================================================
*/

#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <EEPROM.h>

// --- Pin Configurations ---
#define SDA_PIN 21        // I2C Data
#define SCL_PIN 22        // I2C Clock
#define FSR_LEFT 35       // Analog Input (FSR)
#define FSR_RIGHT 34      // Analog Input (FSR)
#define MOTOR_LEFT 25     // Digital Output
#define MOTOR_RIGHT 26    // Digital Output
#define CALIBRATION_BUTTON 2  // Digital Input (PB2)
#define STATUS_LED 13     // Digital Output

// --- WiFi Configuration ---
const char* WIFI_SSID = "YOUR_WIFI_SSID";        // Configure your WiFi network
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"; // Configure your WiFi password
const char* BACKEND_SERVER = "192.168.1.100";     // Configure backend server IP or use auto-discovery
const int BACKEND_PORT = 8000;

// --- Network Management ---
unsigned long lastWiFiCheck = 0;
unsigned long wifiReconnectInterval = 30000; // Start with 30 seconds
unsigned long maxReconnectInterval = 300000; // Max 5 minutes
bool wifiConnected = false;
int reconnectAttempts = 0;

// --- Device Configuration ---
String deviceId = "ESP32_" + String((uint32_t)ESP.getEfuseMac(), HEX);
String sessionId = "";

// --- Sensor Objects and Variables ---
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
float pitch = 0, roll = 0, yaw = 0;
int fsrLeft = 0, fsrRight = 0;
bool pusherDetected = false;
float confidenceLevel = 0.0;

// --- Calibration Variables ---
struct CalibrationData {
  float baselinePitch;
  float baselineFsrLeft;
  float baselineFsrRight;
  float baselineFsrRatio;
  float pitchStdDev;
  float fsrStdDev;
  unsigned long calibrationTimestamp;
  bool isValid;
};

CalibrationData calibration;
bool calibrationMode = false;
unsigned long calibrationStartTime = 0;
const unsigned long CALIBRATION_DURATION = 30000; // 30 seconds
int calibrationSamples = 0;
float calibrationPitchSum = 0;
float calibrationFsrLeftSum = 0;
float calibrationFsrRightSum = 0;

// Arrays to store samples for standard deviation calculation
#define MAX_CALIBRATION_SAMPLES 300 // 30 seconds * 10Hz
float pitchSamples[MAX_CALIBRATION_SAMPLES];
float fsrRatioSamples[MAX_CALIBRATION_SAMPLES];
int sampleIndex = 0;

// --- Detection Thresholds (will be updated by calibration) ---
float TILT_THRESHOLD = 10.0; // degrees
int PRESSURE_DIFF_THRESHOLD = 300; // FSR difference
unsigned long PERSIST_TIME = 2000; // ms tilt must persist
unsigned long tiltStartTime = 0;
bool tiltDetected = false;

// --- Timing Variables ---
unsigned long lastSensorRead = 0;
unsigned long lastDataTransmission = 0;
const unsigned long SENSOR_INTERVAL = 100; // 100ms = 10Hz
const unsigned long TRANSMISSION_INTERVAL = 150; // 150ms for HTTP POST (within 100-200ms range)

// --- HTTP Retry Logic ---
struct HTTPRetryData {
  String jsonPayload;
  int attemptCount;
  unsigned long nextRetryTime;
  bool hasPendingRetry;
};

HTTPRetryData retryQueue;
const int MAX_RETRY_ATTEMPTS = 3;
const unsigned long RETRY_DELAY_BASE = 1000; // 1 second base delay

// --- Function Prototypes ---
void setupWiFi();
void connectToWiFi();
void handleWiFiReconnection();
bool isWiFiConnected();
void updateStatusLED();

void setupSensors();
void readSensors();
void readIMU();
void readFSR();
bool detectPusherSyndrome();
void activateFeedback(bool state);

void handleCalibration();
void startCalibration();
void performCalibrationSample();
void completeCalibration();
void loadCalibrationFromEEPROM();
void saveCalibrationToEEPROM();

void handleRetryQueue();
bool postSensorData();
bool postSensorDataWithRetry(String jsonPayload);
bool postCalibrationData();
void handleHTTPResponse(int statusCode);
void queueRetry(String jsonPayload);

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("=== Vertex WiFi Client Firmware Starting ===");
  Serial.println("Device ID: " + deviceId);
  
  // Initialize EEPROM for calibration storage
  EEPROM.begin(512);
  
  // Pin configurations
  pinMode(FSR_LEFT, INPUT);
  pinMode(FSR_RIGHT, INPUT);
  pinMode(MOTOR_LEFT, OUTPUT);
  pinMode(MOTOR_RIGHT, OUTPUT);
  pinMode(CALIBRATION_BUTTON, INPUT_PULLUP);
  pinMode(STATUS_LED, OUTPUT);
  
  // Initialize outputs
  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);
  digitalWrite(STATUS_LED, LOW);
  
  // ADC configuration
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  
  // Initialize retry queue
  retryQueue.hasPendingRetry = false;
  retryQueue.attemptCount = 0;
  
  // Initialize sensors
  setupSensors();
  
  // Load calibration data
  loadCalibrationFromEEPROM();
  
  // Initialize WiFi
  setupWiFi();
  
  Serial.println("=== Setup Complete ===");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Handle WiFi connection management
  handleWiFiReconnection();
  
  // Handle calibration button and process
  handleCalibration();
  
  // Read sensors at specified interval
  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = currentTime;
  }
  
  // Handle retry queue first
  handleRetryQueue();
  
  // Transmit data at specified interval (only if WiFi connected and no pending retries)
  if (wifiConnected && !retryQueue.hasPendingRetry && 
      (currentTime - lastDataTransmission >= TRANSMISSION_INTERVAL)) {
    if (postSensorData()) {
      lastDataTransmission = currentTime;
    }
  }
  
  // Update status LED
  updateStatusLED();
  
  // Small delay to prevent watchdog issues
  delay(10);
}

// === WiFi Management Functions ===

void setupWiFi() {
  Serial.println("Setting up WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false); // We'll handle reconnection manually
  connectToWiFi();
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startTime < 10000) {
    delay(500);
    Serial.print(".");
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    reconnectAttempts = 0;
    wifiReconnectInterval = 30000; // Reset to 30 seconds
    
    Serial.println();
    Serial.println("WiFi connected successfully!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    wifiConnected = false;
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

void handleWiFiReconnection() {
  unsigned long currentTime = millis();
  
  // Check WiFi status
  if (WiFi.status() != WL_CONNECTED) {
    wifiConnected = false;
  }
  
  // Attempt reconnection if needed
  if (!wifiConnected && (currentTime - lastWiFiCheck >= wifiReconnectInterval)) {
    lastWiFiCheck = currentTime;
    reconnectAttempts++;
    
    Serial.print("WiFi reconnection attempt #");
    Serial.println(reconnectAttempts);
    
    connectToWiFi();
    
    // Exponential backoff with maximum interval
    if (!wifiConnected) {
      wifiReconnectInterval = min(wifiReconnectInterval * 2, maxReconnectInterval);
      Serial.print("Next reconnection attempt in ");
      Serial.print(wifiReconnectInterval / 1000);
      Serial.println(" seconds");
    }
  }
}

bool isWiFiConnected() {
  return wifiConnected && (WiFi.status() == WL_CONNECTED);
}

void updateStatusLED() {
  static unsigned long lastLEDUpdate = 0;
  static bool ledState = false;
  static int blinkCount = 0;
  unsigned long currentTime = millis();
  
  if (calibrationMode) {
    // Fast blinking during calibration with progress indication
    if (currentTime - lastLEDUpdate >= 200) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastLEDUpdate = currentTime;
      
      // Progress indication every 5 seconds
      if (ledState) {
        blinkCount++;
        if (blinkCount % 25 == 0) { // Every 5 seconds (25 blinks * 200ms)
          unsigned long elapsed = currentTime - calibrationStartTime;
          int progress = (elapsed * 100) / CALIBRATION_DURATION;
          Serial.print("Calibration progress: ");
          Serial.print(progress);
          Serial.println("% - Keep holding upright posture");
        }
      }
    }
  } else if (wifiConnected) {
    // Solid on when connected
    digitalWrite(STATUS_LED, HIGH);
    blinkCount = 0;
  } else {
    // Slow blinking when disconnected
    if (currentTime - lastLEDUpdate >= 1000) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastLEDUpdate = currentTime;
      blinkCount = 0;
    }
  }
}

// === Sensor Functions ===

void setupSensors() {
  Serial.println("Initializing sensors...");
  
  // Initialize I2C (same pins as original Vertex_Firmware.ino)
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  delay(1000);
  
  // Initialize BNO055 IMU (same configuration as original)
  if (!bno.begin()) {
    Serial.println("BNO055 initialization failed!");
    // Continue without IMU - use FSR data only (graceful degradation)
  } else {
    Serial.println("BNO055 initialized successfully");
    bno.setExtCrystalUse(true); // External crystal for accuracy (same as original)
  }
}

void readSensors() {
  readIMU();
  readFSR();
  pusherDetected = detectPusherSyndrome();
  activateFeedback(pusherDetected);
  
  // Debug output
  if (Serial) {
    Serial.print("Pitch: ");
    Serial.print(pitch, 1);
    Serial.print("° | FSR L: ");
    Serial.print(fsrLeft);
    Serial.print(" R: ");
    Serial.print(fsrRight);
    Serial.print(" | Pusher: ");
    Serial.print(pusherDetected ? "YES" : "NO");
    Serial.print(" | Confidence: ");
    Serial.println(confidenceLevel, 2);
  }
}

void readIMU() {
  sensors_event_t event;
  if (bno.getEvent(&event)) {
    // Get orientation data (Euler angles)
    pitch = event.orientation.y;
    roll = event.orientation.z;
    yaw = event.orientation.x;
    
    // Handle IMU coordinate system and ensure proper range
    // BNO055 returns pitch in range -180 to +180 degrees
    // Ensure values are within expected range
    if (isnan(pitch)) pitch = 0.0;
    if (isnan(roll)) roll = 0.0;
    if (isnan(yaw)) yaw = 0.0;
  } else {
    // Keep previous values if read fails
    Serial.println("IMU read failed - using previous values");
  }
}

void readFSR() {
  // Read raw values (12-bit ADC: 0-4095 range)
  int rawLeft = analogRead(FSR_LEFT);
  int rawRight = analogRead(FSR_RIGHT);
  
  // Ensure values are within valid range
  rawLeft = constrain(rawLeft, 0, 4095);
  rawRight = constrain(rawRight, 0, 4095);
  
  // Apply filtering (same as original Vertex_Firmware.ino)
  static float fsrLeftFiltered = 0;
  static float fsrRightFiltered = 0;
  
  fsrLeftFiltered = 0.8 * fsrLeftFiltered + 0.2 * rawLeft;
  fsrRightFiltered = 0.8 * fsrRightFiltered + 0.2 * rawRight;
  
  fsrLeft = (int)fsrLeftFiltered;
  fsrRight = (int)fsrRightFiltered;
  
  // Ensure final values are within 0-4095 range as required
  fsrLeft = constrain(fsrLeft, 0, 4095);
  fsrRight = constrain(fsrRight, 0, 4095);
}

bool detectPusherSyndrome() {
  // Use calibrated baseline if available
  float adjustedPitch = pitch;
  float dynamicTiltThreshold = TILT_THRESHOLD;
  float dynamicPressureThreshold = PRESSURE_DIFF_THRESHOLD;
  
  if (calibration.isValid) {
    // Apply patient-specific thresholds using baseline ± 2 standard deviations
    adjustedPitch = pitch - calibration.baselinePitch;
    
    // Dynamic tilt threshold based on calibrated baseline ± 2 SD
    dynamicTiltThreshold = max(5.0, 2.0 * calibration.pitchStdDev);
    
    // Dynamic pressure threshold based on calibrated FSR baseline ± 2 SD
    float currentFsrRatio = (float)fsrRight / (fsrLeft + fsrRight + 1); // +1 to avoid division by zero
    float fsrRatioDiff = abs(currentFsrRatio - calibration.baselineFsrRatio);
    
    // Use FSR ratio difference instead of absolute difference for better accuracy
    if (fsrRatioDiff > (2.0 * calibration.fsrStdDev / 1000.0)) { // Convert to ratio scale
      dynamicPressureThreshold = 0; // Force asymmetric detection when ratio is significantly different
    }
  }
  
  // 1. Check tilt magnitude using dynamic threshold
  bool tilted = abs(adjustedPitch) > dynamicTiltThreshold;
  
  // 2. Check pressure imbalance using dynamic threshold
  int pressureDiff = abs(fsrLeft - fsrRight);
  bool asymmetric = pressureDiff > dynamicPressureThreshold;
  
  // 3. Check persistence (clinical requirement: ≥2 seconds)
  if (tilted) {
    if (!tiltDetected) {
      tiltDetected = true;
      tiltStartTime = millis();
    }
    
    // Must persist for required time (2000ms for clinical accuracy)
    if (millis() - tiltStartTime > PERSIST_TIME) {
      if (asymmetric) {
        // Calculate confidence level based on calibrated thresholds
        float tiltFactor = min(1.0, abs(adjustedPitch) / (dynamicTiltThreshold * 2.0));
        float pressureFactor = min(1.0, (float)pressureDiff / (dynamicPressureThreshold * 2.0 + 1));
        confidenceLevel = (tiltFactor + pressureFactor) / 2.0;
        confidenceLevel = max(0.2, min(1.0, confidenceLevel)); // Ensure range 0.2-1.0
        
        return true; // Pusher behavior detected
      }
    }
  } else {
    tiltDetected = false;
  }
  
  confidenceLevel = 0.0;
  return false;
}

void activateFeedback(bool state) {
  if (!state) {
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, LOW);
    return;
  }
  
  // Same logic as original Vertex_Firmware.ino
  int diff = fsrLeft - fsrRight;
  
  if (diff > PRESSURE_DIFF_THRESHOLD) {
    // Pushing LEFT → vibrate RIGHT (same as original)
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, HIGH);
  } else if (diff < -PRESSURE_DIFF_THRESHOLD) {
    // Pushing RIGHT → vibrate LEFT (same as original)
    digitalWrite(MOTOR_LEFT, HIGH);
    digitalWrite(MOTOR_RIGHT, LOW);
  } else {
    // No significant imbalance - turn off motors (same as original)
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, LOW);
  }
}

// === Calibration Functions ===

void handleCalibration() {
  // Check for calibration button press
  if (digitalRead(CALIBRATION_BUTTON) == LOW) {
    delay(50); // Debounce
    if (digitalRead(CALIBRATION_BUTTON) == LOW && !calibrationMode) {
      startCalibration();
    }
  }
  
  // Handle calibration process
  if (calibrationMode) {
    unsigned long currentTime = millis();
    
    if (currentTime - calibrationStartTime < CALIBRATION_DURATION) {
      // Continue calibration sampling
      performCalibrationSample();
      
      // Progress indication
      if (Serial && (currentTime - calibrationStartTime) % 5000 == 0) {
        int progress = ((currentTime - calibrationStartTime) * 100) / CALIBRATION_DURATION;
        Serial.print("Calibration progress: ");
        Serial.print(progress);
        Serial.println("%");
      }
    } else {
      // Complete calibration
      completeCalibration();
    }
  }
}

void startCalibration() {
  Serial.println("=== Starting 30-second calibration ===");
  Serial.println("PATIENT INSTRUCTION: Please maintain normal upright posture");
  Serial.println("Stay still and upright for the next 30 seconds...");
  Serial.println("LED will blink rapidly during calibration");
  
  calibrationMode = true;
  calibrationStartTime = millis();
  calibrationSamples = 0;
  calibrationPitchSum = 0;
  calibrationFsrLeftSum = 0;
  calibrationFsrRightSum = 0;
  sampleIndex = 0;
  
  // Clear sample arrays
  for (int i = 0; i < MAX_CALIBRATION_SAMPLES; i++) {
    pitchSamples[i] = 0;
    fsrRatioSamples[i] = 0;
  }
  
  // Stop motors during calibration
  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);
  
  // Audio cue simulation via serial (in real implementation, could use buzzer)
  Serial.println("BEEP - Calibration started");
}

void performCalibrationSample() {
  static unsigned long lastSample = 0;
  unsigned long currentTime = millis();
  
  // Sample at 10Hz during calibration (meets 5-10 Hz requirement)
  if (currentTime - lastSample >= 100) {
    if (sampleIndex < MAX_CALIBRATION_SAMPLES) {
      // Store individual samples for standard deviation calculation
      pitchSamples[sampleIndex] = pitch;
      
      // Calculate FSR ratio for this sample
      float totalFsr = fsrLeft + fsrRight + 1; // +1 to avoid division by zero
      fsrRatioSamples[sampleIndex] = (float)fsrRight / totalFsr;
      
      // Accumulate sums for mean calculation
      calibrationSamples++;
      calibrationPitchSum += pitch;
      calibrationFsrLeftSum += fsrLeft;
      calibrationFsrRightSum += fsrRight;
      
      sampleIndex++;
    }
    lastSample = currentTime;
  }
}

void completeCalibration() {
  Serial.println("=== Calibration Complete ===");
  Serial.println("BEEP BEEP - Calibration finished");
  
  if (calibrationSamples > 0) {
    // Calculate baseline values (mean)
    calibration.baselinePitch = calibrationPitchSum / calibrationSamples;
    calibration.baselineFsrLeft = calibrationFsrLeftSum / calibrationSamples;
    calibration.baselineFsrRight = calibrationFsrRightSum / calibrationSamples;
    
    float totalBaseline = calibration.baselineFsrLeft + calibration.baselineFsrRight;
    calibration.baselineFsrRatio = (totalBaseline > 0) ? 
                                   calibration.baselineFsrRight / totalBaseline : 0.5;
    
    // Calculate standard deviations for patient-specific thresholds
    float pitchVarianceSum = 0;
    float fsrRatioVarianceSum = 0;
    
    for (int i = 0; i < calibrationSamples && i < MAX_CALIBRATION_SAMPLES; i++) {
      // Pitch standard deviation
      float pitchDiff = pitchSamples[i] - calibration.baselinePitch;
      pitchVarianceSum += pitchDiff * pitchDiff;
      
      // FSR ratio standard deviation
      float fsrRatioDiff = fsrRatioSamples[i] - calibration.baselineFsrRatio;
      fsrRatioVarianceSum += fsrRatioDiff * fsrRatioDiff;
    }
    
    // Calculate standard deviations
    calibration.pitchStdDev = sqrt(pitchVarianceSum / calibrationSamples);
    calibration.fsrStdDev = sqrt(fsrRatioVarianceSum / calibrationSamples) * 1000; // Scale for easier use
    
    // Ensure minimum thresholds for safety
    calibration.pitchStdDev = max(1.0, calibration.pitchStdDev);
    calibration.fsrStdDev = max(10.0, calibration.fsrStdDev);
    
    calibration.calibrationTimestamp = millis();
    calibration.isValid = true;
    
    // Save to EEPROM
    saveCalibrationToEEPROM();
    
    // Send to backend
    if (wifiConnected) {
      postCalibrationData();
    }
    
    Serial.println("Calibration Results:");
    Serial.print("  Samples collected: ");
    Serial.println(calibrationSamples);
    Serial.print("  Baseline Pitch: ");
    Serial.print(calibration.baselinePitch, 2);
    Serial.println("°");
    Serial.print("  Pitch Std Dev: ");
    Serial.print(calibration.pitchStdDev, 2);
    Serial.println("°");
    Serial.print("  Baseline FSR Left: ");
    Serial.println(calibration.baselineFsrLeft, 0);
    Serial.print("  Baseline FSR Right: ");
    Serial.println(calibration.baselineFsrRight, 0);
    Serial.print("  Baseline FSR Ratio: ");
    Serial.println(calibration.baselineFsrRatio, 3);
    Serial.print("  FSR Std Dev: ");
    Serial.println(calibration.fsrStdDev, 2);
    Serial.print("  Normal Weight Distribution: ");
    Serial.print(calibration.baselineFsrRatio * 100, 1);
    Serial.println("% right");
    
    // Calculate and display patient-specific thresholds
    float tiltThreshold = 2.0 * calibration.pitchStdDev;
    Serial.print("  Applied Tilt Threshold: ±");
    Serial.print(tiltThreshold, 1);
    Serial.println("° from baseline");
    
  } else {
    Serial.println("Calibration failed - no samples collected");
  }
  
  calibrationMode = false;
}

void loadCalibrationFromEEPROM() {
  EEPROM.get(0, calibration);
  
  // Validate calibration data
  if (calibration.calibrationTimestamp == 0 || 
      isnan(calibration.baselinePitch) || 
      calibration.baselineFsrLeft < 0 || 
      calibration.baselineFsrRight < 0) {
    
    Serial.println("No valid calibration found in EEPROM");
    calibration.isValid = false;
  } else {
    Serial.println("Loaded calibration from EEPROM");
    Serial.print("  Calibration date: ");
    Serial.println(calibration.calibrationTimestamp);
  }
}

void saveCalibrationToEEPROM() {
  EEPROM.put(0, calibration);
  EEPROM.commit();
  Serial.println("Calibration saved to EEPROM");
}

// === HTTP Communication Functions ===

void handleRetryQueue() {
  if (!retryQueue.hasPendingRetry || !isWiFiConnected()) {
    return;
  }
  
  unsigned long currentTime = millis();
  if (currentTime >= retryQueue.nextRetryTime) {
    Serial.print("Retrying HTTP POST (attempt ");
    Serial.print(retryQueue.attemptCount + 1);
    Serial.print("/");
    Serial.print(MAX_RETRY_ATTEMPTS);
    Serial.println(")");
    
    bool success = postSensorDataWithRetry(retryQueue.jsonPayload);
    
    if (success) {
      // Success - clear retry queue
      retryQueue.hasPendingRetry = false;
      retryQueue.attemptCount = 0;
      Serial.println("Retry successful!");
    } else {
      retryQueue.attemptCount++;
      
      if (retryQueue.attemptCount >= MAX_RETRY_ATTEMPTS) {
        // Max retries reached - give up
        Serial.println("Max retry attempts reached - dropping packet");
        retryQueue.hasPendingRetry = false;
        retryQueue.attemptCount = 0;
      } else {
        // Schedule next retry with exponential backoff
        unsigned long delay = RETRY_DELAY_BASE * (1 << retryQueue.attemptCount); // 1s, 2s, 4s
        retryQueue.nextRetryTime = currentTime + delay;
        Serial.print("Next retry in ");
        Serial.print(delay / 1000);
        Serial.println(" seconds");
      }
    }
  }
}

void queueRetry(String jsonPayload) {
  if (!retryQueue.hasPendingRetry) {
    retryQueue.jsonPayload = jsonPayload;
    retryQueue.attemptCount = 0;
    retryQueue.nextRetryTime = millis() + RETRY_DELAY_BASE;
    retryQueue.hasPendingRetry = true;
    Serial.println("Queued for retry");
  }
}

bool postSensorData() {
  if (!isWiFiConnected()) {
    return false;
  }
  
  // Create JSON payload with enhanced precision and required fields
  DynamicJsonDocument doc(512);
  doc["device_id"] = deviceId;
  doc["session_id"] = sessionId.length() > 0 ? sessionId : nullptr;
  doc["timestamp"] = millis();
  
  // Pitch data with 0.1 degree precision in range -180 to +180 degrees
  float normalizedPitch = pitch;
  while (normalizedPitch > 180.0) normalizedPitch -= 360.0;
  while (normalizedPitch < -180.0) normalizedPitch += 360.0;
  doc["pitch"] = round(normalizedPitch * 10) / 10.0;
  
  doc["roll"] = round(roll * 10) / 10.0;
  doc["yaw"] = round(yaw * 10) / 10.0;
  
  // FSR values in range 0-4095 with timestamp
  doc["fsr_left"] = constrain(fsrLeft, 0, 4095);
  doc["fsr_right"] = constrain(fsrRight, 0, 4095);
  
  // Pusher detection boolean status and confidence level
  doc["pusher_detected"] = pusherDetected;
  doc["confidence_level"] = round(confidenceLevel * 100) / 100.0;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  bool success = postSensorDataWithRetry(jsonString);
  
  if (!success && !retryQueue.hasPendingRetry) {
    // Queue for retry if not already queued
    queueRetry(jsonString);
  }
  
  return success;
}

bool postSensorDataWithRetry(String jsonPayload) {
  HTTPClient http;
  String url = "http://" + String(BACKEND_SERVER) + ":" + String(BACKEND_PORT) + "/api/sensor-data";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000); // 5 second timeout
  
  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  handleHTTPResponse(httpResponseCode);
  
  http.end();
  
  return (httpResponseCode == 200);
}

bool postCalibrationData() {
  if (!isWiFiConnected() || !calibration.isValid) {
    return false;
  }
  
  HTTPClient http;
  String url = "http://" + String(BACKEND_SERVER) + ":" + String(BACKEND_PORT) + "/api/calibration/complete";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(512);
  doc["device_id"] = deviceId;
  doc["patient_id"] = "default"; // Would be configured per patient
  doc["baseline_pitch"] = calibration.baselinePitch;
  doc["baseline_fsr_left"] = calibration.baselineFsrLeft;
  doc["baseline_fsr_right"] = calibration.baselineFsrRight;
  doc["baseline_fsr_ratio"] = calibration.baselineFsrRatio;
  doc["pitch_std_dev"] = calibration.pitchStdDev;
  doc["fsr_std_dev"] = calibration.fsrStdDev;
  doc["calibration_timestamp"] = calibration.calibrationTimestamp;
  doc["is_active"] = true;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send POST request
  int httpResponseCode = http.POST(jsonString);
  
  handleHTTPResponse(httpResponseCode);
  
  http.end();
  
  return (httpResponseCode == 200);
}

void handleHTTPResponse(int statusCode) {
  static int consecutiveFailures = 0;
  
  if (statusCode == 200) {
    consecutiveFailures = 0;
    // Success - could update session ID from response if needed
  } else if (statusCode > 0) {
    consecutiveFailures++;
    Serial.print("HTTP Error: ");
    Serial.println(statusCode);
    
    if (consecutiveFailures >= 3) {
      Serial.println("Multiple HTTP failures - checking network connection");
      wifiConnected = false; // Force reconnection check
    }
  } else {
    consecutiveFailures++;
    Serial.print("HTTP Connection Error: ");
    Serial.println(statusCode);
    
    if (consecutiveFailures >= 3) {
      wifiConnected = false; // Force reconnection check
    }
  }
}