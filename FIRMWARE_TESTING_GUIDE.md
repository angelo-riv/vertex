# ESP32 Firmware Testing & Development Guide

This guide focuses on testing and developing the ESP32 firmware code for the Vertex Rehabilitation System, with instructions for both hardware and simulation testing.

## 🔧 Hardware Requirements

### ESP32 Development Board
- **Board**: ESP32 Dev Module (30-pin)
- **Microcontroller**: ESP32-WROOM-32
- **Flash**: 4MB minimum
- **RAM**: 520KB SRAM

### Sensors & Components
- **IMU**: BNO055 9-DOF sensor (I2C)
- **FSR**: 2x Force Sensitive Resistors (Analog)
- **Actuators**: 2x Vibration motors (Digital PWM)
- **Button**: Calibration pushbutton (Digital input)
- **LED**: Status indicator (Digital output)

### Wiring Diagram
```
ESP32 Pin Connections:
├── GPIO21 (SDA) → BNO055 SDA
├── GPIO22 (SCL) → BNO055 SCL  
├── GPIO36 (A0)  → FSR Left (via 10kΩ resistor)
├── GPIO39 (A3)  → FSR Right (via 10kΩ resistor)
├── GPIO18      → Vibration Motor 1 (PWM)
├── GPIO19      → Vibration Motor 2 (PWM)
├── GPIO23      → Calibration Button (Pull-up)
├── GPIO2       → Status LED
├── 3.3V        → BNO055 VIN, Pull-up resistors
└── GND         → All component grounds
```

## 🚀 Quick Start

### 1. Arduino IDE Setup
```bash
# Install Arduino IDE (if not installed)
# Download from: https://www.arduino.cc/en/software

# Add ESP32 Board Manager URL:
# File → Preferences → Additional Board Manager URLs:
https://dl.espressif.com/dl/package_esp32_index.json

# Install ESP32 boards:
# Tools → Board → Boards Manager → Search "ESP32" → Install
```

### 2. Install Required Libraries
```bash
# In Arduino IDE:
# Tools → Manage Libraries → Install:
- Adafruit Unified Sensor
- Adafruit BNO055
- WiFi (built-in)
- HTTPClient (built-in)
- ArduinoJson
```

### 3. Configure Arduino IDE
```bash
# Tools → Board → ESP32 Arduino → ESP32 Dev Module
# Tools → Port → Select your ESP32 port (COM3, /dev/ttyUSB0, etc.)
# Tools → Upload Speed → 921600
# Tools → CPU Frequency → 240MHz (WiFi/BT)
# Tools → Flash Size → 4MB (32Mb)
# Tools → Partition Scheme → Default 4MB with spiffs
```

## 📁 Firmware Code Structure

### Main Firmware File
```
firmware/
├── Vertex_WiFi_Client.ino     # Main firmware code
├── README.md                  # Hardware setup guide
└── tests/                     # Test files
    ├── test_wifi_client_reliability.ino
    ├── test_calibration_functionality.ino
    ├── test_calibration_data_processing.ino
    └── test_esp32_data_transmission.ino
```

### Key Code Sections in Vertex_WiFi_Client.ino
```cpp
// 1. Pin Definitions (Lines 1-20)
#define SDA_PIN 21
#define SCL_PIN 22
#define FSR_LEFT_PIN 36
// ... etc

// 2. WiFi Configuration (Lines 25-40)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://192.168.1.100:8000";

// 3. Sensor Initialization (Lines 45-80)
Adafruit_BNO055 bno = Adafruit_BNO055(55);

// 4. Main Loop (Lines 200-300)
void loop() {
  readSensors();
  sendDataToServer();
  delay(200); // 5Hz transmission rate
}
```

## 🧪 Testing Without Hardware

### Option 1: Use ESP32 Simulator
```bash
# Start backend first
cd backend
uvicorn main:app --reload

# Run ESP32 simulator (simulates firmware behavior)
python esp32_simulator.py --scenario normal --interval 0.2
```

### Option 2: Firmware Test Suite
```bash
# Run firmware tests without hardware
cd firmware/tests
python test_wifi_integration.py
python test_esp32_data_transmission.py
python test_calibration_data_processing.py
```

### Option 3: Arduino IDE Serial Monitor Simulation
```cpp
// Add this to your .ino file for testing without sensors:
#define SIMULATION_MODE 1

void readSensors() {
  #ifdef SIMULATION_MODE
    // Simulate sensor readings
    pitch = random(-15, 15);
    roll = random(-10, 10);
    fsrLeft = random(1500, 2500);
    fsrRight = random(1500, 2500);
  #else
    // Real sensor code here
  #endif
}
```

## 🔌 Testing With Hardware

### Prerequisites
Before testing with hardware, ensure you have:
- ESP32 Dev Module (30-pin recommended)
- BNO055 IMU sensor breakout board
- 2x Force Sensitive Resistors (FSRs)
- 2x 10kΩ resistors (for FSR voltage dividers)
- 2x Vibration motors (optional)
- Pushbutton for calibration
- LED for status indication
- Breadboard and jumper wires
- USB cable for ESP32 programming

### Hardware Assembly Guide

#### Step 1: Power Connections
```
ESP32 Power Rails:
├── 3.3V → Breadboard positive rail
├── GND  → Breadboard negative rail
└── Connect all components to these rails
```

#### Step 2: BNO055 IMU Wiring
```
BNO055 → ESP32
├── VIN → 3.3V
├── GND → GND
├── SDA → GPIO21 (I2C Data)
└── SCL → GPIO22 (I2C Clock)
```

#### Step 3: FSR Sensor Wiring
```
FSR Left (Voltage Divider):
├── FSR → 3.3V
├── FSR → GPIO36 (A0) + 10kΩ resistor to GND

FSR Right (Voltage Divider):
├── FSR → 3.3V  
├── FSR → GPIO39 (A3) + 10kΩ resistor to GND
```

#### Step 4: Control Components
```
Additional Components:
├── Calibration Button → GPIO23 (with internal pull-up)
├── Status LED → GPIO2 (with 220Ω resistor to GND)
├── Vibration Motor 1 → GPIO18 (optional)
└── Vibration Motor 2 → GPIO19 (optional)
```

### Hardware Testing Procedure

#### Test 1: Basic Hardware Validation
Upload this diagnostic code first to verify all connections:

```cpp
// Hardware Diagnostic Test Code
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55);

void setup() {
  Serial.begin(115200);
  Serial.println("🔧 ESP32 Hardware Diagnostic Test");
  Serial.println("==================================");
  
  // Initialize pins
  pinMode(2, OUTPUT);   // Status LED
  pinMode(23, INPUT_PULLUP);  // Calibration button
  
  // Test 1: I2C and BNO055
  Serial.println("Testing I2C and BNO055...");
  Wire.begin(21, 22);
  
  if (!bno.begin()) {
    Serial.println("❌ BNO055 not detected! Check wiring:");
    Serial.println("   - VIN to 3.3V");
    Serial.println("   - GND to GND"); 
    Serial.println("   - SDA to GPIO21");
    Serial.println("   - SCL to GPIO22");
  } else {
    Serial.println("✅ BNO055 connected successfully");
    
    // Display sensor details
    sensor_t sensor;
    bno.getSensor(&sensor);
    Serial.println("Sensor: " + String(sensor.name));
    Serial.println("Version: " + String(sensor.version));
  }
  
  // Test 2: FSR sensors
  Serial.println("\nTesting FSR sensors...");
  int fsrLeft = analogRead(36);
  int fsrRight = analogRead(39);
  
  Serial.println("FSR Left (GPIO36): " + String(fsrLeft));
  Serial.println("FSR Right (GPIO39): " + String(fsrRight));
  
  if (fsrLeft == 0 && fsrRight == 0) {
    Serial.println("❌ FSR sensors not detected! Check:");
    Serial.println("   - FSR connections to 3.3V");
    Serial.println("   - 10kΩ pull-down resistors to GND");
    Serial.println("   - Analog pins GPIO36 and GPIO39");
  } else {
    Serial.println("✅ FSR sensors responding");
  }
  
  // Test 3: Button and LED
  Serial.println("\nTesting button and LED...");
  digitalWrite(2, HIGH);  // Turn on LED
  
  if (digitalRead(23) == LOW) {
    Serial.println("✅ Calibration button is pressed");
  } else {
    Serial.println("⚪ Calibration button is not pressed");
  }
  
  Serial.println("✅ Status LED should be ON");
  Serial.println("\n🎯 Press calibration button to test...");
}

void loop() {
  // Continuous sensor monitoring
  static unsigned long lastPrint = 0;
  
  if (millis() - lastPrint > 1000) {  // Print every second
    Serial.println("\n--- LIVE SENSOR DATA ---");
    
    // IMU data
    sensors_event_t event;
    bno.getEvent(&event);
    
    Serial.println("IMU - Pitch: " + String(event.orientation.y, 2) + 
                   "° | Roll: " + String(event.orientation.z, 2) + 
                   "° | Yaw: " + String(event.orientation.x, 2) + "°");
    
    // FSR data
    int fsrLeft = analogRead(36);
    int fsrRight = analogRead(39);
    Serial.println("FSR - Left: " + String(fsrLeft) + " | Right: " + String(fsrRight));
    
    // Button state
    bool buttonPressed = (digitalRead(23) == LOW);
    Serial.println("Button: " + String(buttonPressed ? "PRESSED" : "Released"));
    
    // Blink LED to show activity
    digitalWrite(2, !digitalRead(2));
    
    lastPrint = millis();
  }
  
  // Test calibration button
  if (digitalRead(23) == LOW) {
    Serial.println("🎯 CALIBRATION BUTTON PRESSED!");
    
    // Rapid LED blink for feedback
    for (int i = 0; i < 6; i++) {
      digitalWrite(2, HIGH);
      delay(100);
      digitalWrite(2, LOW);
      delay(100);
    }
  }
}
```

#### Test 2: WiFi Connectivity Test
After hardware validation, test WiFi connectivity:

```cpp
// WiFi Connection Test
#include <WiFi.h>

const char* ssid = "YOUR_WIFI_SSID";        // Replace with your WiFi
const char* password = "YOUR_WIFI_PASSWORD"; // Replace with your password

void setup() {
  Serial.begin(115200);
  Serial.println("📡 WiFi Connection Test");
  Serial.println("=======================");
  
  pinMode(2, OUTPUT);  // Status LED
  
  // Start WiFi connection
  WiFi.begin(ssid, password);
  Serial.print("Connecting to: " + String(ssid));
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(2, !digitalRead(2));  // Blink LED while connecting
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi Connected Successfully!");
    Serial.println("IP Address: " + WiFi.localIP().toString());
    Serial.println("Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    Serial.println("MAC Address: " + WiFi.macAddress());
    digitalWrite(2, HIGH);  // Solid LED = connected
  } else {
    Serial.println("\n❌ WiFi Connection Failed!");
    Serial.println("Check:");
    Serial.println("   - SSID and password are correct");
    Serial.println("   - WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)");
    Serial.println("   - Router is within range");
    
    // Fast blink = connection failed
    while (true) {
      digitalWrite(2, HIGH);
      delay(200);
      digitalWrite(2, LOW);
      delay(200);
    }
  }
}

void loop() {
  // Monitor WiFi connection
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("📶 WiFi Status: Connected | IP: " + WiFi.localIP().toString() + 
                   " | RSSI: " + String(WiFi.RSSI()) + " dBm");
  } else {
    Serial.println("❌ WiFi Status: Disconnected");
    digitalWrite(2, LOW);
  }
  
  delay(5000);  // Check every 5 seconds
}
```

#### Test 3: Backend Communication Test
Test HTTP communication with the backend:

```cpp
// Backend Communication Test
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverURL = "http://192.168.1.100:8000";  // Replace with your backend IP

void setup() {
  Serial.begin(115200);
  Serial.println("🌐 Backend Communication Test");
  Serial.println("=============================");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected: " + WiFi.localIP().toString());
  
  // Test backend connectivity
  testBackendConnection();
}

void testBackendConnection() {
  HTTPClient http;
  
  // Test 1: Health endpoint
  Serial.println("\n🏥 Testing backend health endpoint...");
  http.begin(String(serverURL) + "/api/health");
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("✅ Backend health check passed");
    Serial.println("Response: " + response);
  } else {
    Serial.println("❌ Backend health check failed: " + String(httpCode));
    Serial.println("Check:");
    Serial.println("   - Backend server is running (uvicorn main:app --reload)");
    Serial.println("   - Server IP address is correct: " + String(serverURL));
    Serial.println("   - Port 8000 is accessible");
  }
  http.end();
  
  // Test 2: Sensor data endpoint
  Serial.println("\n📡 Testing sensor data endpoint...");
  
  // Create test sensor data
  DynamicJsonDocument doc(1024);
  doc["deviceId"] = "ESP32_TEST_001";
  doc["timestamp"] = millis();
  doc["pitch"] = 5.5;
  doc["roll"] = 2.1;
  doc["yaw"] = 0.8;
  doc["fsrLeft"] = 2048;
  doc["fsrRight"] = 2048;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  http.begin(String(serverURL) + "/api/sensor-data");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-ID", "ESP32_TEST_001");
  http.addHeader("X-Device-Signature", "test_signature");
  http.addHeader("X-Timestamp", String(millis()));
  
  httpCode = http.POST(jsonString);
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("✅ Sensor data sent successfully");
    Serial.println("Response: " + response);
    
    // Parse response to check clinical analysis
    DynamicJsonDocument responseDoc(1024);
    deserializeJson(responseDoc, response);
    
    if (responseDoc.containsKey("clinical_analysis")) {
      JsonObject clinical = responseDoc["clinical_analysis"];
      Serial.println("Clinical Analysis:");
      Serial.println("   Pusher Detected: " + String(clinical["pusher_detected"].as<bool>() ? "Yes" : "No"));
      Serial.println("   Clinical Score: " + String(clinical["clinical_score"].as<float>()));
      Serial.println("   Tilt Classification: " + String(clinical["tilt_classification"].as<String>()));
    }
  } else {
    Serial.println("❌ Sensor data transmission failed: " + String(httpCode));
    String response = http.getString();
    Serial.println("Error response: " + response);
  }
  http.end();
}

void loop() {
  // Send test data every 10 seconds
  delay(10000);
  Serial.println("\n🔄 Sending periodic test data...");
  testBackendConnection();
}
```

#### Test 4: Full System Integration Test
Finally, upload the complete Vertex_WiFi_Client.ino and test the full system:

```bash
# 1. Configure the firmware
# Edit Vertex_WiFi_Client.ino:
# - Set your WiFi SSID and password (lines 25-30)
# - Set your backend server IP (line 35)
# - Verify pin assignments match your wiring (lines 10-20)

# 2. Upload firmware to ESP32
# - Open Vertex_WiFi_Client.ino in Arduino IDE
# - Select Board: ESP32 Dev Module
# - Select correct COM port
# - Click Upload

# 3. Start backend server
cd backend
uvicorn main:app --reload

# 4. Start frontend (optional)
cd frontend
npm start

# 5. Open Serial Monitor (115200 baud)
# You should see:
```

Expected Serial Monitor Output:
```
🚀 Vertex WiFi Client Starting...
📡 Connecting to WiFi: YOUR_WIFI_SSID
✅ WiFi connected! IP: 192.168.1.150
✅ BNO055 initialized successfully
🎯 Calibration button ready on GPIO23
📊 Starting sensor data transmission...

=== SENSOR DATA ===
Timestamp: 1234567890
Pitch: +2.5° | Roll: +1.2° | Yaw: +0.8°
FSR Left: 2048 | FSR Right: 2048 | Ratio: 1.00
📡 Sending to server... Response: 200
🟢 NORMAL | Clinical Score: 0

=== SENSOR DATA ===
Timestamp: 1234567891
Pitch: +12.5° | Roll: +3.2° | Yaw: +1.1°
FSR Left: 1800 | FSR Right: 2300 | Ratio: 0.78
📡 Sending to server... Response: 200
🔴 PUSHER DETECTED | Clinical Score: 2
```

### Hardware Testing Checklist

#### Pre-Upload Checklist
- [ ] All components wired according to diagram
- [ ] Power connections verified (3.3V and GND)
- [ ] I2C connections correct (SDA=21, SCL=22)
- [ ] FSR voltage dividers properly connected
- [ ] WiFi credentials configured in code
- [ ] Backend server IP address set correctly
- [ ] Arduino IDE configured for ESP32 Dev Module

#### Post-Upload Verification
- [ ] Serial Monitor shows WiFi connection success
- [ ] BNO055 sensor initializes without errors
- [ ] FSR sensors show reasonable values (not 0 or 4095)
- [ ] HTTP requests return status 200
- [ ] Backend receives and processes sensor data
- [ ] Website shows real-time updates from ESP32
- [ ] Calibration button triggers calibration mode
- [ ] Status LED indicates connection state correctly

#### Functional Testing
- [ ] **Posture Detection**: Tilt ESP32 and verify pitch/roll changes
- [ ] **Weight Distribution**: Press FSRs and verify value changes
- [ ] **Pusher Detection**: Create >10° tilt and verify pusher alert
- [ ] **Calibration**: Press button and complete 30-second calibration
- [ ] **Network Recovery**: Disconnect/reconnect WiFi and verify recovery
- [ ] **Data Continuity**: Verify consistent data transmission over time

### Troubleshooting Hardware Issues

#### ESP32 Won't Upload
```bash
Solutions:
1. Hold BOOT button while clicking Upload
2. Press EN button after upload completes
3. Check USB cable (must be data cable, not charge-only)
4. Try different USB port
5. Reduce upload speed: Tools → Upload Speed → 115200
6. Check driver installation for CP2102/CH340 chip
```

#### BNO055 Not Detected
```bash
Check:
1. Wiring: VIN→3.3V, GND→GND, SDA→21, SCL→22
2. I2C address conflicts (BNO055 uses 0x28 or 0x29)
3. Power supply (BNO055 needs stable 3.3V)
4. Try different I2C pins if needed
5. Check for loose connections on breadboard
```

#### FSR Sensors Reading 0 or 4095
```bash
Check:
1. Voltage divider: FSR→3.3V, FSR+10kΩ→GPIO, 10kΩ→GND
2. Analog pin connections (GPIO36, GPIO39)
3. Resistor values (should be 10kΩ)
4. FSR physical connection and pressure
5. Try different analog pins if needed
```

#### WiFi Connection Fails
```bash
Check:
1. SSID and password spelling (case-sensitive)
2. WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)
3. Router distance and signal strength
4. Network security type (WPA2 recommended)
5. Try mobile hotspot for testing
```

#### Backend Communication Fails
```bash
Check:
1. Backend server is running (uvicorn main:app --reload)
2. Server IP address is correct in firmware
3. Port 8000 is accessible (check firewall)
4. ESP32 and server are on same network
5. Try ping from ESP32 IP to server IP
```

### Performance Validation

#### Expected Performance Metrics
- **Data Transmission Rate**: 5Hz (every 200ms)
- **HTTP Response Time**: <100ms typical
- **WiFi Connection Time**: <10 seconds
- **Sensor Reading Accuracy**: ±0.1° for IMU, ±10 for FSR
- **Memory Usage**: <50% of available heap
- **Power Consumption**: <200mA during transmission

#### Long-term Stability Test
```bash
# Run for 1+ hours to verify:
1. No memory leaks (heap usage stable)
2. Consistent transmission timing
3. WiFi connection remains stable
4. Sensor readings remain accurate
5. No unexpected resets or crashes
```

This comprehensive hardware testing guide ensures your ESP32 firmware works reliably with real sensors and communicates properly with the backend system.

## ⚙️ Editing Firmware Code

### Key Configuration Areas

#### 1. WiFi Settings (Lines 25-30)
```cpp
// Edit these for your network:
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password
const char* serverURL = "http://192.168.1.100:8000";  // Backend server IP
```

#### 2. Sensor Calibration (Lines 150-180)
```cpp
// Adjust these based on your hardware:
#define FSR_THRESHOLD_MIN 100    // Minimum FSR reading
#define FSR_THRESHOLD_MAX 4000   // Maximum FSR reading
#define PITCH_OFFSET 0.0         // IMU pitch calibration offset
#define ROLL_OFFSET 0.0          // IMU roll calibration offset
```

#### 3. Transmission Settings (Lines 200-220)
```cpp
// Adjust data transmission:
#define TRANSMISSION_INTERVAL 200  // Milliseconds between transmissions
#define MAX_RETRY_ATTEMPTS 3       // HTTP request retry attempts
#define REQUEST_TIMEOUT 5000       // HTTP timeout in milliseconds
```

#### 4. Clinical Thresholds (Lines 250-270)
```cpp
// Local pusher detection thresholds:
#define NORMAL_THRESHOLD 5.0      // Normal posture range (±degrees)
#define PUSHER_THRESHOLD 10.0     // Pusher syndrome threshold
#define SEVERE_THRESHOLD 20.0     // Severe pusher threshold
```

### Common Modifications

#### Add Debug Output
```cpp
// Add this for more detailed debugging:
#define DEBUG_MODE 1

void debugPrint(String message) {
  #ifdef DEBUG_MODE
    Serial.print("[DEBUG] ");
    Serial.println(message);
  #endif
}
```

#### Change Transmission Rate
```cpp
// For faster/slower data transmission:
void loop() {
  readSensors();
  sendDataToServer();
  
  // Options:
  delay(100);  // 10Hz - High frequency
  delay(200);  // 5Hz - Standard (recommended)
  delay(500);  // 2Hz - Low frequency
  delay(1000); // 1Hz - Very low frequency
}
```

#### Add Custom Sensor Processing
```cpp
// Add sensor filtering:
float filterPitch(float rawPitch) {
  static float filteredPitch = 0;
  float alpha = 0.1; // Low-pass filter coefficient
  
  filteredPitch = alpha * rawPitch + (1 - alpha) * filteredPitch;
  return filteredPitch;
}
```

## 🌐 Website Testing

### Quick Website Startup
```bash
# 1. Start Backend (Required)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload

# 2. Start Frontend (Optional - for full UI)
cd frontend
npm install
npm start

# 3. Open browser to:
# Backend API: http://localhost:8000
# Frontend UI: http://localhost:3000
```

### Website Testing Options

#### Option 1: Backend Only (API Testing)
```bash
# Start just the backend
cd backend
uvicorn main:app --reload

# Test API endpoints:
curl http://localhost:8000/api/health
curl http://localhost:8000/docs  # Interactive API documentation
```

#### Option 2: Full Website (Backend + Frontend)
```bash
# Terminal 1: Backend
cd backend
uvicorn main:app --reload

# Terminal 2: Frontend  
cd frontend
npm start

# Open browser: http://localhost:3000
```

#### Option 3: Demo Mode Testing
```bash
# Start backend, then enable demo mode:
curl -X POST http://localhost:8000/api/demo/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "scenario": "pusher_syndrome"}'

# Website will show simulated ESP32 data
```

### Website Features to Test

#### 1. Real-time Monitoring Dashboard
- **PostureVisualization**: Shows body lean direction
- **CircularTiltMeter**: Displays tilt angles with clinical thresholds
- **SensorDataDisplay**: Shows FSR values and device connection
- **AlertMessage**: Displays pusher syndrome detection alerts

#### 2. Device Connection Status
- **Connection indicators**: Green (connected) / Red (disconnected)
- **Data freshness**: Shows last update timestamp
- **Demo mode toggle**: Switch between real and simulated data

#### 3. Calibration Interface
- **Start Calibration**: Triggers 30-second calibration process
- **Progress display**: Shows calibration countdown and progress
- **Results display**: Shows baseline values after calibration

## 🔍 Troubleshooting

### ESP32 Issues

#### Upload Fails
```bash
# Solutions:
1. Hold BOOT button while uploading
2. Check USB cable (data cable, not charge-only)
3. Try different USB port
4. Reduce upload speed: Tools → Upload Speed → 115200
5. Press EN button after upload
```

#### WiFi Connection Fails
```cpp
// Add WiFi diagnostics:
void diagnoseWiFi() {
  Serial.println("WiFi Status: " + String(WiFi.status()));
  Serial.println("SSID: " + String(ssid));
  Serial.println("Signal Strength: " + String(WiFi.RSSI()));
  
  // Try different WiFi settings:
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
}
```

#### Sensor Not Working
```cpp
// Test individual sensors:
void testSensors() {
  // Test BNO055
  if (!bno.begin()) {
    Serial.println("❌ Check BNO055 wiring (SDA=21, SCL=22)");
  }
  
  // Test FSRs
  int fsr1 = analogRead(36);
  int fsr2 = analogRead(39);
  Serial.println("FSR readings: " + String(fsr1) + ", " + String(fsr2));
  
  if (fsr1 == 0 && fsr2 == 0) {
    Serial.println("❌ Check FSR wiring and pull-up resistors");
  }
}
```

### Website Issues

#### Backend Won't Start
```bash
# Check Python version (3.8+ required)
python --version

# Install dependencies
pip install fastapi uvicorn

# Try different port
uvicorn main:app --reload --port 8001
```

#### Frontend Won't Start
```bash
# Check Node.js version (14+ required)
node --version

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Try different port
npm start -- --port 3001
```

#### No Data on Website
```bash
# Check if backend is receiving data:
curl http://localhost:8000/api/demo/status

# Enable demo mode:
curl -X POST http://localhost:8000/api/demo/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

## 📊 Testing Checklist

### Firmware Testing
- [ ] Code compiles without errors
- [ ] ESP32 connects to WiFi
- [ ] Sensors read valid data
- [ ] HTTP requests reach backend
- [ ] Serial monitor shows expected output
- [ ] Calibration button works
- [ ] Status LED indicates connection state

### Website Testing  
- [ ] Backend starts successfully (port 8000)
- [ ] Frontend loads (port 3000)
- [ ] API endpoints respond
- [ ] Real-time data updates
- [ ] Demo mode works
- [ ] WebSocket connection established
- [ ] Clinical algorithms detect pusher syndrome

### Integration Testing
- [ ] ESP32 data appears on website
- [ ] Pusher syndrome alerts trigger
- [ ] Calibration workflow completes
- [ ] Multiple devices can connect
- [ ] Connection status updates correctly

## 🎯 Next Steps

1. **Start with simulation** - Test website without hardware
2. **Build hardware** - Wire ESP32 with sensors
3. **Upload firmware** - Flash Vertex_WiFi_Client.ino
4. **Test connectivity** - Verify WiFi and sensor readings
5. **Integrate with website** - See real-time data on dashboard
6. **Clinical testing** - Validate pusher syndrome detection
7. **Calibration testing** - Test patient-specific baselines

The system is designed to work with or without hardware, so you can develop and test the complete system using simulation, then seamlessly transition to real hardware when ready!