# ESP32 Firmware Development Notes

## 🔧 Key Firmware Configuration Areas

### WiFi & Network Settings
```cpp
// Lines 25-35 in Vertex_WiFi_Client.ino
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://192.168.1.100:8000";  // Change to your backend IP

// Network timeout settings
#define WIFI_TIMEOUT 10000        // WiFi connection timeout (ms)
#define HTTP_TIMEOUT 5000         // HTTP request timeout (ms)
#define RECONNECT_INTERVAL 30000  // Auto-reconnect interval (ms)
```

### Sensor Configuration
```cpp
// Pin assignments (Lines 10-20)
#define SDA_PIN 21               // I2C Data pin for BNO055
#define SCL_PIN 22               // I2C Clock pin for BNO055
#define FSR_LEFT_PIN 36          // Left FSR analog input
#define FSR_RIGHT_PIN 39         // Right FSR analog input
#define CALIBRATION_BUTTON 23    // Calibration button input
#define STATUS_LED 2             // Status LED output
#define VIBRATION_MOTOR_1 18     // Left vibration motor PWM
#define VIBRATION_MOTOR_2 19     // Right vibration motor PWM

// Sensor calibration values (Lines 150-170)
#define FSR_MIN_VALUE 100        // Minimum valid FSR reading
#define FSR_MAX_VALUE 4000       // Maximum valid FSR reading
#define PITCH_CALIBRATION 0.0    // IMU pitch offset
#define ROLL_CALIBRATION 0.0     // IMU roll offset
```

### Data Transmission Settings
```cpp
// Transmission timing (Lines 200-210)
#define TRANSMISSION_RATE 200    // Milliseconds between data sends (5Hz)
#define MAX_RETRIES 3           // HTTP request retry attempts
#define RETRY_DELAY 1000        // Delay between retries (ms)

// Data packet structure
struct SensorData {
  String deviceId;
  unsigned long timestamp;
  float pitch;
  float roll;
  float yaw;
  int fsrLeft;
  int fsrRight;
};
```

## 🎯 Critical Code Sections to Modify

### 1. Device Identification
```cpp
// Line 40 - Change device ID for each ESP32
String deviceId = "ESP32_VERTEX_001";  // Make unique for each device

// For multiple devices, use MAC address:
String getDeviceId() {
  String mac = WiFi.macAddress();
  mac.replace(":", "");
  return "ESP32_" + mac.substring(6);  // Last 6 chars of MAC
}
```

### 2. Clinical Thresholds (Local Processing)
```cpp
// Lines 250-280 - Local pusher detection
#define NORMAL_THRESHOLD 5.0     // ±5° normal range
#define PUSHER_THRESHOLD 10.0    // ≥10° pusher syndrome
#define SEVERE_THRESHOLD 20.0    // ≥20° severe pusher
#define FSR_IMBALANCE_THRESHOLD 0.3  // 30% weight imbalance

bool detectPusherSyndrome(float pitch, int fsrLeft, int fsrRight) {
  // Check tilt angle
  if (abs(pitch) < PUSHER_THRESHOLD) return false;
  
  // Check weight distribution
  float ratio = (float)fsrLeft / fsrRight;
  float imbalance = abs(1.0 - ratio);
  
  return (imbalance > FSR_IMBALANCE_THRESHOLD);
}
```

### 3. Calibration Process
```cpp
// Lines 300-350 - 30-second calibration
void performCalibration() {
  Serial.println("🎯 Starting 30-second calibration...");
  
  float pitchSum = 0, rollSum = 0;
  int fsrLeftSum = 0, fsrRightSum = 0;
  int samples = 0;
  
  unsigned long startTime = millis();
  
  while (millis() - startTime < 30000) {  // 30 seconds
    // Read sensors
    sensors_event_t event;
    bno.getEvent(&event);
    
    pitchSum += event.orientation.y;
    rollSum += event.orientation.z;
    fsrLeftSum += analogRead(FSR_LEFT_PIN);
    fsrRightSum += analogRead(FSR_RIGHT_PIN);
    samples++;
    
    // Blink LED during calibration
    digitalWrite(STATUS_LED, (millis() / 500) % 2);
    
    delay(100);  // 10Hz sampling during calibration
  }
  
  // Calculate baselines
  baselinePitch = pitchSum / samples;
  baselineRoll = rollSum / samples;
  baselineFsrLeft = fsrLeftSum / samples;
  baselineFsrRight = fsrRightSum / samples;
  
  Serial.println("✅ Calibration complete!");
  Serial.println("Baseline Pitch: " + String(baselinePitch));
  Serial.println("Baseline FSR L/R: " + String(baselineFsrLeft) + "/" + String(baselineFsrRight));
  
  // Save to EEPROM (optional)
  saveCalibrationToEEPROM();
}
```

### 4. Error Handling & Recovery
```cpp
// Lines 400-450 - Robust error handling
void handleWiFiDisconnection() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("📡 WiFi disconnected, attempting reconnection...");
    
    digitalWrite(STATUS_LED, LOW);  // LED off = disconnected
    
    WiFi.disconnect();
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n✅ WiFi reconnected!");
      digitalWrite(STATUS_LED, HIGH);
    } else {
      Serial.println("\n❌ WiFi reconnection failed");
    }
  }
}

void handleSensorError() {
  if (!bno.begin()) {
    Serial.println("❌ BNO055 sensor error - check wiring");
    
    // Blink LED rapidly to indicate sensor error
    for (int i = 0; i < 10; i++) {
      digitalWrite(STATUS_LED, HIGH);
      delay(100);
      digitalWrite(STATUS_LED, LOW);
      delay(100);
    }
    
    // Try to reinitialize
    Wire.begin(SDA_PIN, SCL_PIN);
    delay(1000);
  }
}
```

## 🔍 Debugging & Monitoring

### Serial Monitor Output
```cpp
// Add comprehensive debug output
void printSystemStatus() {
  Serial.println("=== SYSTEM STATUS ===");
  Serial.println("Device ID: " + deviceId);
  Serial.println("WiFi SSID: " + String(ssid));
  Serial.println("WiFi IP: " + WiFi.localIP().toString());
  Serial.println("WiFi RSSI: " + String(WiFi.RSSI()) + " dBm");
  Serial.println("Server URL: " + String(serverURL));
  Serial.println("Uptime: " + String(millis() / 1000) + " seconds");
  Serial.println("Free Heap: " + String(ESP.getFreeHeap()) + " bytes");
  Serial.println("====================");
}
```

### LED Status Indicators
```cpp
// Visual status feedback
void updateStatusLED() {
  if (WiFi.status() != WL_CONNECTED) {
    // Slow blink = WiFi disconnected
    digitalWrite(STATUS_LED, (millis() / 1000) % 2);
  } else if (lastHttpSuccess + 10000 < millis()) {
    // Fast blink = HTTP errors
    digitalWrite(STATUS_LED, (millis() / 200) % 2);
  } else {
    // Solid on = all good
    digitalWrite(STATUS_LED, HIGH);
  }
}
```

### Performance Monitoring
```cpp
// Track performance metrics
unsigned long lastTransmission = 0;
unsigned long transmissionCount = 0;
unsigned long errorCount = 0;

void logPerformanceMetrics() {
  if (millis() - lastMetricsLog > 60000) {  // Every minute
    float successRate = ((float)(transmissionCount - errorCount) / transmissionCount) * 100;
    
    Serial.println("📊 PERFORMANCE METRICS:");
    Serial.println("Transmissions: " + String(transmissionCount));
    Serial.println("Errors: " + String(errorCount));
    Serial.println("Success Rate: " + String(successRate) + "%");
    Serial.println("Avg Interval: " + String((millis() - startTime) / transmissionCount) + "ms");
    
    lastMetricsLog = millis();
  }
}
```

## ⚡ Performance Optimization

### Memory Management
```cpp
// Optimize memory usage
void optimizeMemory() {
  // Use String sparingly, prefer char arrays
  char jsonBuffer[512];  // Fixed size buffer
  
  // Clear unused variables
  if (millis() % 60000 == 0) {  // Every minute
    ESP.gc();  // Force garbage collection
  }
  
  // Monitor heap usage
  if (ESP.getFreeHeap() < 10000) {  // Less than 10KB free
    Serial.println("⚠️ Low memory warning: " + String(ESP.getFreeHeap()));
  }
}
```

### Power Management
```cpp
// Battery optimization for wearable use
void optimizePower() {
  // Reduce CPU frequency when idle
  setCpuFrequencyMhz(80);  // 80MHz instead of 240MHz
  
  // Use light sleep between transmissions
  if (millis() - lastTransmission > TRANSMISSION_RATE - 50) {
    esp_light_sleep_start();
  }
  
  // Turn off unused peripherals
  // WiFi.setSleep(true);  // Enable WiFi sleep (careful with connectivity)
}
```

### Sensor Filtering
```cpp
// Implement sensor filtering for stable readings
class SensorFilter {
private:
  float alpha = 0.1;  // Low-pass filter coefficient
  float filteredPitch = 0;
  float filteredRoll = 0;
  
public:
  void update(float pitch, float roll) {
    filteredPitch = alpha * pitch + (1 - alpha) * filteredPitch;
    filteredRoll = alpha * roll + (1 - alpha) * filteredRoll;
  }
  
  float getPitch() { return filteredPitch; }
  float getRoll() { return filteredRoll; }
};

SensorFilter filter;
```

## 🛠️ Common Modifications

### Change Transmission Rate
```cpp
// For different update frequencies:
#define TRANSMISSION_RATE 100   // 10Hz - High frequency
#define TRANSMISSION_RATE 200   // 5Hz - Standard (recommended)
#define TRANSMISSION_RATE 500   // 2Hz - Low frequency
#define TRANSMISSION_RATE 1000  // 1Hz - Very low frequency
```

### Add Custom Sensors
```cpp
// Example: Add heart rate sensor
#define HEART_RATE_PIN 34

int readHeartRate() {
  // Read heart rate sensor
  int rawValue = analogRead(HEART_RATE_PIN);
  
  // Convert to BPM (sensor-specific calculation)
  int bpm = map(rawValue, 0, 4095, 60, 180);
  
  return bpm;
}

// Add to JSON payload:
// "heartRate": readHeartRate()
```

### Implement Local Haptic Feedback
```cpp
// Vibration motor control for immediate feedback
void triggerHapticFeedback(float pitch) {
  if (abs(pitch) > PUSHER_THRESHOLD) {
    // Vibrate motors based on lean direction
    if (pitch > 0) {
      // Lean right - vibrate left motor
      analogWrite(VIBRATION_MOTOR_1, 255);
      analogWrite(VIBRATION_MOTOR_2, 0);
    } else {
      // Lean left - vibrate right motor
      analogWrite(VIBRATION_MOTOR_1, 0);
      analogWrite(VIBRATION_MOTOR_2, 255);
    }
    
    delay(200);  // Vibrate for 200ms
    
    // Turn off motors
    analogWrite(VIBRATION_MOTOR_1, 0);
    analogWrite(VIBRATION_MOTOR_2, 0);
  }
}
```

## 🔒 Security Considerations

### Device Authentication
```cpp
// Generate device signature for authentication
String generateSignature(String data, String timestamp) {
  String message = deviceId + ":" + timestamp + ":" + data;
  
  // Simple HMAC-like signature (use proper crypto library in production)
  String secret = "device-secret-key";  // Should be unique per device
  
  // Hash the message (simplified - use proper HMAC in production)
  return String(message.hashCode(), HEX);
}
```

### Data Encryption (Optional)
```cpp
// Basic XOR encryption for sensitive data
String encryptData(String data, String key) {
  String encrypted = "";
  
  for (int i = 0; i < data.length(); i++) {
    char encryptedChar = data[i] ^ key[i % key.length()];
    encrypted += encryptedChar;
  }
  
  return encrypted;
}
```

## 📝 Testing Checklist

### Before Upload
- [ ] WiFi credentials are correct
- [ ] Server URL matches backend IP
- [ ] Pin assignments match hardware
- [ ] Device ID is unique
- [ ] Transmission rate is appropriate

### After Upload
- [ ] Serial monitor shows WiFi connection
- [ ] Sensor readings are reasonable
- [ ] HTTP requests return 200 status
- [ ] Backend receives data
- [ ] Website shows real-time updates
- [ ] Calibration button works
- [ ] Status LED indicates connection state

### Performance Validation
- [ ] Memory usage is stable
- [ ] No memory leaks over time
- [ ] Transmission timing is consistent
- [ ] Error rate is low (<5%)
- [ ] Battery life is acceptable

This firmware is designed to be robust, efficient, and easy to modify for different hardware configurations and clinical requirements.