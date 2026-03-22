/*
=========================================================
Vertex Firmware - WiFi Integrated

REQUIRED ARDUINO SETTINGS:
--------------------------------
Tools → Board → ESP32 Dev Module
Tools → Port  → Select your COM port
Serial Monitor Baud Rate → 115200

REQUIRED LIBRARIES (Install via Tools → Manage Libraries):
--------------------------------
1. ArduinoJson
2. HTTPClient (ESP32 built-in)

WIRING (MPU6050 → ESP32):
--------------------------------
VIN  → 3.3V
GND  → GND
SDA  → GPIO21
SCL  → GPIO22
FSR1 → GPIO35 (Left)
FSR2 → GPIO34 (Right)
MOTOR_LEFT  → GPIO25
MOTOR_RIGHT → GPIO26
CALIB_BTN   → GPIO2  (with pull-up resistor)
STATUS_LED  → GPIO13

IMPORTANT:
- Set WIFI_SSID and WIFI_PASSWORD before uploading
- Set BACKEND_SERVER to your backend machine's local IP
- USB power is sufficient for testing
=========================================================
*/

#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include <math.h>

// --- Pin Configurations ---
#define SDA_PIN 21
#define SCL_PIN 22
#define FSR_LEFT 35
#define FSR_RIGHT 34
#define MOTOR_LEFT 25
#define MOTOR_RIGHT 26
#define CALIBRATION_BUTTON 2
#define STATUS_LED 13

// --- MPU6050 ---
const int MPU = 0x68;
int16_t AcX, AcY, AcZ;
int16_t GyX, GyY, GyZ;

// --- WiFi / Backend Configuration ---
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_SERVER = "192.168.1.100";   // Your backend machine's local IP
const int   BACKEND_PORT   = 8000;

// --- Network State ---
bool wifiConnected = false;
int  reconnectAttempts = 0;
unsigned long lastWiFiCheck        = 0;
unsigned long wifiReconnectInterval = 30000;
const unsigned long MAX_RECONNECT_INTERVAL = 300000;

// --- Device Identity ---
String deviceId  = "ESP32_" + String((uint32_t)ESP.getEfuseMac(), HEX);
String sessionId = "";

// --- Sensor Readings ---
float roll    = 0;
int   fsrLeft  = 0;
int   fsrRight = 0;
bool  pusherDetected = false;
float confidenceLevel = 0.0;

// --- Detection Thresholds ---
int   TILT_THRESHOLD          = 10;   // degrees
int   PRESSURE_DIFF_THRESHOLD = 300;  // FSR raw difference
unsigned long PERSIST_TIME    = 1500; // ms tilt must persist
unsigned long tiltStartTime   = 0;
bool  tiltDetected = false;

// --- Calibration ---
struct CalibrationData {
  float baselineRoll;
  float baselineFsrLeft;
  float baselineFsrRight;
  float baselineFsrRatio;
  float rollStdDev;
  float fsrStdDev;
  unsigned long calibrationTimestamp;
  bool isValid;
};

CalibrationData calibration;
bool  calibrationMode      = false;
unsigned long calibrationStartTime = 0;
const unsigned long CALIBRATION_DURATION = 30000; // 30 seconds
int   calibrationSamples   = 0;
float calibrationRollSum   = 0;
float calibrationFsrLeftSum  = 0;
float calibrationFsrRightSum = 0;

#define MAX_CALIBRATION_SAMPLES 300
float rollSamples[MAX_CALIBRATION_SAMPLES];
float fsrRatioSamples[MAX_CALIBRATION_SAMPLES];
int   sampleIndex = 0;

// --- Timing ---
unsigned long lastSensorRead      = 0;
unsigned long lastDataTransmission = 0;
const unsigned long SENSOR_INTERVAL      = 50;  // 20 Hz (matches original delay(50))
const unsigned long TRANSMISSION_INTERVAL = 150; // ~6-7 Hz HTTP POST

// --- HTTP Retry ---
struct HTTPRetryData {
  String jsonPayload;
  int    attemptCount;
  unsigned long nextRetryTime;
  bool   hasPendingRetry;
};

HTTPRetryData retryQueue;
const int MAX_RETRY_ATTEMPTS = 3;
const unsigned long RETRY_DELAY_BASE = 1000;

// --- Prototypes ---
void setupWiFi();
void connectToWiFi();
void handleWiFiReconnection();
bool isWiFiConnected();
void updateStatusLED();

void setupSensors();
void readSensors();
void imuRead();
void fsrRead();
bool detectPusher();
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

// =========================
// SETUP
// =========================
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("=== Vertex Firmware Starting ===");
  Serial.println("Device ID: " + deviceId);

  EEPROM.begin(512);

  pinMode(FSR_LEFT, INPUT);
  pinMode(FSR_RIGHT, INPUT);
  pinMode(MOTOR_LEFT, OUTPUT);
  pinMode(MOTOR_RIGHT, OUTPUT);
  pinMode(CALIBRATION_BUTTON, INPUT_PULLUP);
  pinMode(STATUS_LED, OUTPUT);

  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);
  digitalWrite(STATUS_LED, LOW);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  retryQueue.hasPendingRetry = false;
  retryQueue.attemptCount    = 0;

  setupSensors();
  loadCalibrationFromEEPROM();
  setupWiFi();

  Serial.println("=== Setup Complete ===");
}

// =========================
// LOOP
// =========================
void loop() {
  unsigned long now = millis();

  handleWiFiReconnection();
  handleCalibration();

  if (now - lastSensorRead >= SENSOR_INTERVAL) {
    readSensors();
    lastSensorRead = now;
  }

  handleRetryQueue();

  if (wifiConnected && !retryQueue.hasPendingRetry &&
      (now - lastDataTransmission >= TRANSMISSION_INTERVAL)) {
    if (postSensorData()) {
      lastDataTransmission = now;
    }
  }

  updateStatusLED();
}

// =========================
// SENSOR SETUP
// =========================
void setupSensors() {
  Serial.println("Initializing MPU6050...");

  Wire.begin(SDA_PIN, SCL_PIN);

  // Wake up MPU6050
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  Serial.println("MPU6050 Initialized");
}

// =========================
// READ SENSORS
// =========================
void readSensors() {
  imuRead();
  fsrRead();
  pusherDetected = detectPusher();
  activateFeedback(pusherDetected);

  Serial.print("Roll: ");
  Serial.print(roll, 1);
  Serial.print(" | L: ");
  Serial.print(fsrLeft);
  Serial.print(" | R: ");
  Serial.print(fsrRight);
  Serial.print(" | Pusher: ");
  Serial.print(pusherDetected ? "YES" : "NO");
  Serial.print(" | Conf: ");
  Serial.println(confidenceLevel, 2);
}

// =========================
// MPU6050 READ
// =========================
void imuRead() {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, 14, true);

  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // skip temp
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();

  float ay = AcY;
  float az = AcZ;
  roll = atan2(ay, az) * 180.0 / PI;
}

// =========================
// FSR READ
// =========================
void fsrRead() {
  int rawLeft  = analogRead(FSR_LEFT);
  int rawRight = analogRead(FSR_RIGHT);

  rawLeft  = constrain(rawLeft,  0, 4095);
  rawRight = constrain(rawRight, 0, 4095);

  static float fsrLeftFiltered  = 0;
  static float fsrRightFiltered = 0;

  fsrLeftFiltered  = 0.8 * fsrLeftFiltered  + 0.2 * rawLeft;
  fsrRightFiltered = 0.8 * fsrRightFiltered + 0.2 * rawRight;

  fsrLeft  = constrain((int)fsrLeftFiltered,  0, 4095);
  fsrRight = constrain((int)fsrRightFiltered, 0, 4095);
}

// =========================
// PUSHER DETECTION
// =========================
bool detectPusher() {
  // Apply calibrated baseline offset if available
  float adjustedRoll = roll;
  float dynamicTiltThreshold     = TILT_THRESHOLD;
  float dynamicPressureThreshold = PRESSURE_DIFF_THRESHOLD;

  if (calibration.isValid) {
    adjustedRoll = roll - calibration.baselineRoll;
    dynamicTiltThreshold = max(5.0f, 2.0f * calibration.rollStdDev);

    float currentFsrRatio = (float)fsrRight / (fsrLeft + fsrRight + 1);
    float fsrRatioDiff = abs(currentFsrRatio - calibration.baselineFsrRatio);
    if (fsrRatioDiff > (2.0f * calibration.fsrStdDev / 1000.0f)) {
      dynamicPressureThreshold = 0;
    }
  }

  // 1. Directional tilt check (left OR right)
  bool tiltedLeft  = adjustedRoll < -dynamicTiltThreshold;
  bool tiltedRight = adjustedRoll >  dynamicTiltThreshold;
  bool tilted = tiltedLeft || tiltedRight;

  // 2. Pressure imbalance
  int pressureDiff = abs(fsrLeft - fsrRight);
  bool asymmetric  = pressureDiff > dynamicPressureThreshold;

  // 3. Persistence check
  if (tilted) {
    if (!tiltDetected) {
      tiltDetected  = true;
      tiltStartTime = millis();
    }

    if (millis() - tiltStartTime > PERSIST_TIME) {
      if (asymmetric) {
        float tiltFactor    = min(1.0f, abs(adjustedRoll) / (dynamicTiltThreshold * 2.0f));
        float pressureFactor = min(1.0f, (float)pressureDiff / (dynamicPressureThreshold * 2.0f + 1));
        confidenceLevel = max(0.2f, min(1.0f, (tiltFactor + pressureFactor) / 2.0f));
        return true;
      }
    }
  } else {
    tiltDetected = false;
  }

  confidenceLevel = 0.0;
  return false;
}

// =========================
// MOTOR FEEDBACK
// =========================
void activateFeedback(bool state) {
  if (!state) {
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, LOW);
    return;
  }

  int diff = fsrLeft - fsrRight;

  if (diff > PRESSURE_DIFF_THRESHOLD) {
    // Pushing LEFT → vibrate RIGHT
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, HIGH);
  } else if (diff < -PRESSURE_DIFF_THRESHOLD) {
    // Pushing RIGHT → vibrate LEFT
    digitalWrite(MOTOR_LEFT, HIGH);
    digitalWrite(MOTOR_RIGHT, LOW);
  } else {
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, LOW);
  }
}

// =========================
// WIFI MANAGEMENT
// =========================
void setupWiFi() {
  Serial.println("Setting up WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(false);
  connectToWiFi();
}

void connectToWiFi() {
  Serial.print("Connecting to: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    reconnectAttempts = 0;
    wifiReconnectInterval = 30000;
    Serial.println();
    Serial.print("Connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println("\nWiFi connection failed.");
  }
}

void handleWiFiReconnection() {
  unsigned long now = millis();
  if (WiFi.status() != WL_CONNECTED) wifiConnected = false;

  if (!wifiConnected && (now - lastWiFiCheck >= wifiReconnectInterval)) {
    lastWiFiCheck = now;
    reconnectAttempts++;
    Serial.print("Reconnect attempt #");
    Serial.println(reconnectAttempts);
    connectToWiFi();

    if (!wifiConnected) {
      wifiReconnectInterval = min(wifiReconnectInterval * 2UL, MAX_RECONNECT_INTERVAL);
    }
  }
}

bool isWiFiConnected() {
  return wifiConnected && (WiFi.status() == WL_CONNECTED);
}

void updateStatusLED() {
  static unsigned long lastLEDUpdate = 0;
  static bool ledState = false;
  unsigned long now = millis();

  if (calibrationMode) {
    if (now - lastLEDUpdate >= 200) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastLEDUpdate = now;
    }
  } else if (wifiConnected) {
    digitalWrite(STATUS_LED, HIGH);
  } else {
    if (now - lastLEDUpdate >= 1000) {
      ledState = !ledState;
      digitalWrite(STATUS_LED, ledState);
      lastLEDUpdate = now;
    }
  }
}

// =========================
// CALIBRATION
// =========================
void handleCalibration() {
  if (digitalRead(CALIBRATION_BUTTON) == LOW) {
    delay(50);
    if (digitalRead(CALIBRATION_BUTTON) == LOW && !calibrationMode) {
      startCalibration();
    }
  }

  if (calibrationMode) {
    unsigned long now = millis();
    if (now - calibrationStartTime < CALIBRATION_DURATION) {
      performCalibrationSample();
    } else {
      completeCalibration();
    }
  }
}

void startCalibration() {
  Serial.println("=== Starting 30-second calibration ===");
  Serial.println("Maintain normal upright posture for 30 seconds...");

  calibrationMode      = true;
  calibrationStartTime = millis();
  calibrationSamples   = 0;
  calibrationRollSum   = 0;
  calibrationFsrLeftSum  = 0;
  calibrationFsrRightSum = 0;
  sampleIndex = 0;

  for (int i = 0; i < MAX_CALIBRATION_SAMPLES; i++) {
    rollSamples[i]     = 0;
    fsrRatioSamples[i] = 0;
  }

  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);
}

void performCalibrationSample() {
  static unsigned long lastSample = 0;
  unsigned long now = millis();

  if (now - lastSample >= 100 && sampleIndex < MAX_CALIBRATION_SAMPLES) {
    rollSamples[sampleIndex] = roll;
    float total = fsrLeft + fsrRight + 1;
    fsrRatioSamples[sampleIndex] = (float)fsrRight / total;

    calibrationSamples++;
    calibrationRollSum     += roll;
    calibrationFsrLeftSum  += fsrLeft;
    calibrationFsrRightSum += fsrRight;
    sampleIndex++;
    lastSample = now;
  }
}

void completeCalibration() {
  Serial.println("=== Calibration Complete ===");

  if (calibrationSamples > 0) {
    calibration.baselineRoll     = calibrationRollSum / calibrationSamples;
    calibration.baselineFsrLeft  = calibrationFsrLeftSum / calibrationSamples;
    calibration.baselineFsrRight = calibrationFsrRightSum / calibrationSamples;

    float total = calibration.baselineFsrLeft + calibration.baselineFsrRight;
    calibration.baselineFsrRatio = (total > 0) ? calibration.baselineFsrRight / total : 0.5;

    float rollVarSum = 0, fsrRatioVarSum = 0;
    for (int i = 0; i < calibrationSamples && i < MAX_CALIBRATION_SAMPLES; i++) {
      float rd = rollSamples[i] - calibration.baselineRoll;
      rollVarSum += rd * rd;
      float fd = fsrRatioSamples[i] - calibration.baselineFsrRatio;
      fsrRatioVarSum += fd * fd;
    }

    calibration.rollStdDev = max(1.0f, sqrt(rollVarSum / calibrationSamples));
    calibration.fsrStdDev  = max(10.0f, sqrt(fsrRatioVarSum / calibrationSamples) * 1000.0f);
    calibration.calibrationTimestamp = millis();
    calibration.isValid = true;

    saveCalibrationToEEPROM();
    if (wifiConnected) postCalibrationData();

    Serial.print("Baseline Roll: ");   Serial.print(calibration.baselineRoll, 2);   Serial.println("°");
    Serial.print("Roll StdDev: ");     Serial.print(calibration.rollStdDev, 2);     Serial.println("°");
    Serial.print("FSR Ratio: ");       Serial.print(calibration.baselineFsrRatio * 100, 1); Serial.println("% right");
  } else {
    Serial.println("Calibration failed - no samples.");
  }

  calibrationMode = false;
}

void loadCalibrationFromEEPROM() {
  EEPROM.get(0, calibration);
  if (calibration.calibrationTimestamp == 0 || isnan(calibration.baselineRoll)) {
    Serial.println("No valid calibration in EEPROM.");
    calibration.isValid = false;
  } else {
    Serial.println("Calibration loaded from EEPROM.");
  }
}

void saveCalibrationToEEPROM() {
  EEPROM.put(0, calibration);
  EEPROM.commit();
  Serial.println("Calibration saved to EEPROM.");
}

// =========================
// HTTP COMMUNICATION
// =========================
bool postSensorData() {
  if (!isWiFiConnected()) return false;

  DynamicJsonDocument doc(512);
  doc["device_id"]       = deviceId;
  doc["session_id"]      = sessionId.length() > 0 ? sessionId : nullptr;
  doc["timestamp"]       = millis();
  doc["roll"]            = round(roll * 10) / 10.0;
  doc["fsr_left"]        = fsrLeft;
  doc["fsr_right"]       = fsrRight;
  doc["pusher_detected"] = pusherDetected;
  doc["confidence_level"] = round(confidenceLevel * 100) / 100.0;

  String json;
  serializeJson(doc, json);

  bool ok = postSensorDataWithRetry(json);
  if (!ok && !retryQueue.hasPendingRetry) queueRetry(json);
  return ok;
}

bool postSensorDataWithRetry(String jsonPayload) {
  HTTPClient http;
  String url = "http://" + String(BACKEND_SERVER) + ":" + String(BACKEND_PORT) + "/api/sensor-data";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  int code = http.POST(jsonPayload);
  handleHTTPResponse(code);
  http.end();

  return (code == 200);
}

bool postCalibrationData() {
  if (!isWiFiConnected() || !calibration.isValid) return false;

  HTTPClient http;
  String url = "http://" + String(BACKEND_SERVER) + ":" + String(BACKEND_PORT) + "/api/calibration/complete";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(512);
  doc["device_id"]              = deviceId;
  doc["patient_id"]             = "default";
  doc["baseline_roll"]          = calibration.baselineRoll;
  doc["baseline_fsr_left"]      = calibration.baselineFsrLeft;
  doc["baseline_fsr_right"]     = calibration.baselineFsrRight;
  doc["baseline_fsr_ratio"]     = calibration.baselineFsrRatio;
  doc["roll_std_dev"]           = calibration.rollStdDev;
  doc["fsr_std_dev"]            = calibration.fsrStdDev;
  doc["calibration_timestamp"]  = calibration.calibrationTimestamp;
  doc["is_active"]              = true;

  String json;
  serializeJson(doc, json);

  int code = http.POST(json);
  handleHTTPResponse(code);
  http.end();

  return (code == 200);
}

void handleRetryQueue() {
  if (!retryQueue.hasPendingRetry || !isWiFiConnected()) return;

  unsigned long now = millis();
  if (now >= retryQueue.nextRetryTime) {
    bool ok = postSensorDataWithRetry(retryQueue.jsonPayload);
    if (ok) {
      retryQueue.hasPendingRetry = false;
      retryQueue.attemptCount    = 0;
    } else {
      retryQueue.attemptCount++;
      if (retryQueue.attemptCount >= MAX_RETRY_ATTEMPTS) {
        Serial.println("Max retries reached - dropping packet.");
        retryQueue.hasPendingRetry = false;
        retryQueue.attemptCount    = 0;
      } else {
        unsigned long backoff = RETRY_DELAY_BASE * (1UL << retryQueue.attemptCount);
        retryQueue.nextRetryTime = now + backoff;
      }
    }
  }
}

void queueRetry(String jsonPayload) {
  if (!retryQueue.hasPendingRetry) {
    retryQueue.jsonPayload     = jsonPayload;
    retryQueue.attemptCount    = 0;
    retryQueue.nextRetryTime   = millis() + RETRY_DELAY_BASE;
    retryQueue.hasPendingRetry = true;
  }
}

void handleHTTPResponse(int statusCode) {
  static int failures = 0;
  if (statusCode == 200) {
    failures = 0;
  } else {
    failures++;
    Serial.print("HTTP error: ");
    Serial.println(statusCode);
    if (failures >= 3) {
      wifiConnected = false;
      failures = 0;
    }
  }
}
