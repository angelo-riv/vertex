#include <Wire.h>

// --- MPU6050 ---
const int MPU = 0x68;
int16_t AcX, AcY, AcZ;
int16_t GyX, GyY, GyZ;

// --- Pin Configurations --- 
#define SDA_PIN 21        
#define SCL_PIN 22        

#define FSR_LEFT 35       
#define FSR_RIGHT 34      

#define MOTOR_LEFT 25     
#define MOTOR_RIGHT 26    

// --- Variables ---
float roll = 0;

int fsrLeft = 0;
int fsrRight = 0;

// Detection Thresholds
int TILT_THRESHOLD = 10;       // degrees (from your MPU code)
int PRESSURE_DIFF_THRESHOLD = 300;
int PERSIST_TIME = 1500;

unsigned long tiltStartTime = 0;
bool tiltDetected = false;

// --- PROTOTYPES ---
void imuRead();
void fsrRead();
bool detectPusher();
void activateFeedback(bool state);

// =========================
// SETUP
// =========================
void setup() {
  Serial.begin(115200);

  Wire.begin(SDA_PIN, SCL_PIN);

  // Wake up MPU6050
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  pinMode(FSR_LEFT, INPUT);
  pinMode(FSR_RIGHT, INPUT);

  pinMode(MOTOR_LEFT, OUTPUT);
  pinMode(MOTOR_RIGHT, OUTPUT);

  digitalWrite(MOTOR_LEFT, LOW);
  digitalWrite(MOTOR_RIGHT, LOW);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  Serial.println("MPU6050 Initialized");
}

// =========================
// LOOP
// =========================
void loop() {
  imuRead();   // <-- NEW
  fsrRead();

  bool pushing = detectPusher();
  activateFeedback(pushing);

  Serial.print("Roll: ");
  Serial.print(roll);
  Serial.print(" | L: ");
  Serial.print(fsrLeft);
  Serial.print(" | R: ");
  Serial.print(fsrRight);
  Serial.print(" | Pusher: ");
  Serial.println(pushing);

  delay(50);
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

  float ax = AcX;
  float ay = AcY;
  float az = AcZ;

  roll = atan2(ay, az) * 180 / PI;
}

// =========================
// FSR READ
// =========================
void fsrRead(){
  int rawLeft  = analogRead(FSR_LEFT);
  int rawRight = analogRead(FSR_RIGHT);

  static float fsrLeftFiltered = 0;
  static float fsrRightFiltered = 0;

  fsrLeftFiltered  = 0.8 * fsrLeftFiltered  + 0.2 * rawLeft;
  fsrRightFiltered = 0.8 * fsrRightFiltered + 0.2 * rawRight;

  fsrLeft  = (int)fsrLeftFiltered;
  fsrRight = (int)fsrRightFiltered;
}

// =========================
// DETECTION LOGIC
// =========================
bool detectPusher() {

  // 1. Check tilt direction
  bool tiltedLeft  = roll < -TILT_THRESHOLD;
  bool tiltedRight = roll >  TILT_THRESHOLD;
  bool tilted = tiltedLeft || tiltedRight;

  // 2. Pressure imbalance
  int pressureDiff = abs(fsrLeft - fsrRight);
  bool asymmetric = pressureDiff > PRESSURE_DIFF_THRESHOLD;

  // 3. Persistence logic
  if (tilted) {
    if (!tiltDetected) {
      tiltDetected = true;
      tiltStartTime = millis();
    }

    if (millis() - tiltStartTime > PERSIST_TIME) {
      if (asymmetric) {
        return true;
      }
    }
  } else {
    tiltDetected = false;
  }

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
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, HIGH);
  }
  else if (diff < -PRESSURE_DIFF_THRESHOLD) {
    digitalWrite(MOTOR_LEFT, HIGH);
    digitalWrite(MOTOR_RIGHT, LOW);
  }
  else {
    digitalWrite(MOTOR_LEFT, LOW);
    digitalWrite(MOTOR_RIGHT, LOW);
  }
}