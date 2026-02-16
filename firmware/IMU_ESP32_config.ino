/*
=========================================================
PROJECT: ESP32 + BNO055 BASELINE CONFIG

REQUIRED ARDUINO SETTINGS:
--------------------------------
Tools → Board → ESP32 Dev Module
Tools → Port  → Select your COM port
Serial Monitor Baud Rate → 115200

REQUIRED LIBRARIES (Install via Tools → Manage Libraries):
--------------------------------
1. Adafruit Unified Sensor
2. Adafruit BNO055

WIRING (BNO055 → ESP32):
--------------------------------
VIN  → 3.3V
GND  → GND
SDA  → GPIO21
SCL  → GPIO22
FSR1 → GPIO34
FSR2 → GPIO35
DRIVER → GPIO25
DRIVER → GPIO26

IMPORTANT:
- USB power is enough for testing
- Do NOT use 5V to power BNO055 logic
=========================================================
*/
//THIS IS THE BASELINE CODE FOR THE CONFIGURATION OF THE PINS FOR WHAT WE NEED AND TO GET THE ESP32 TO READ IMU DATA
//Now we need to add the threshold/posture calibration logic
//Add motor vibration control logic and integrate FSR weight imbalance logic (if needed i think the resistors can handle this)

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

// ================= PIN DEFINITIONS =================
#define SDA_PIN 21        // I2C Data
#define SCL_PIN 22        // I2C Clock

#define FSR_LEFT 35       // Analog Input (FSR)
#define FSR_RIGHT 36      // Analog Input (FSR)

#define MOTOR1 25         // Digital Output
#define MOTOR2 26         // Digital Output

// Create IMU object (default I2C address 0x28)
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);

void setup() {

  // Start Serial Communication
  Serial.begin(115200);
  delay(1000);

  Serial.println("Starting ESP32 + BNO055...");

  // ================= I2C CONFIG =================
  Wire.begin(SDA_PIN, SCL_PIN);   // Define SDA & SCL pins
  Wire.setClock(100000);          // Lower clock for stability

  // ================= IMU INIT =================
  if (!bno.begin()) {
    Serial.println("ERROR: BNO055 NOT DETECTED");
    Serial.println("Check wiring (SDA/SCL swapped? No GND?)");
    while (1);  // Stop here if IMU not found
  }

  bno.setExtCrystalUse(true);
  Serial.println("BNO055 OK");

  // ================= PIN MODES =================
  pinMode(FSR_LEFT, INPUT);
  pinMode(FSR_RIGHT, INPUT);

  pinMode(MOTOR1, OUTPUT);
  pinMode(MOTOR2, OUTPUT);

  digitalWrite(MOTOR1, LOW);
  digitalWrite(MOTOR2, LOW);

  // Set ADC resolution (0–4095)
  analogReadResolution(12);
}

void loop() {

  // Read IMU orientation
  sensors_event_t event;
  bno.getEvent(&event);

  float pitch = event.orientation.y;

  // Read analog FSR values
  int fsrLeft  = analogRead(FSR_LEFT);
  int fsrRight = analogRead(FSR_RIGHT);

  // Print values to Serial Monitor
  Serial.print("Pitch: ");
  Serial.print(pitch);
  Serial.print(" | FSR L: ");
  Serial.print(fsrLeft);
  Serial.print(" | FSR R: ");
  Serial.println(fsrRight);

  delay(100);
}
