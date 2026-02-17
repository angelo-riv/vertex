# Firmware - ESP32 Wearable Device

Arduino-based firmware for the ESP32 microcontroller that powers the chest-strap wearable device for Pusher Syndrome rehabilitation.

## Overview

The wearable device provides:
- Real-time trunk orientation monitoring via BNO055 IMU
- Weight distribution detection through FSR pressure sensors
- Immediate haptic feedback via vibration motors
- Wireless data transmission to clinical backend
- Battery-optimized operation for all-day wear

## Hardware Components

### Sensors
- **BNO055 IMU**: 9-axis absolute orientation sensor for trunk tilt detection
- **2x FSR Sensors**: Force Sensitive Resistors for weight distribution monitoring

### Actuators
- **2x Vibration Motors**: Provide corrective haptic feedback on left/right sides

### Microcontroller
- **ESP32 Dev Module**: Main processing unit with WiFi capability

## Pin Configuration

```cpp
// I2C Communication (BNO055)
#define SDA_PIN 21        // I2C Data
#define SCL_PIN 22        // I2C Clock

// Analog Inputs (FSR Sensors)
#define FSR_LEFT 35       // Left side pressure sensor
#define FSR_RIGHT 34      // Right side pressure sensor

// Digital Outputs (Vibration Motors)
#define MOTOR1 25         // Left side vibration motor
#define MOTOR2 26         // Right side vibration motor
```

## Setup Instructions

### Prerequisites
- Arduino IDE (latest version)
- ESP32 board package installed
- Required libraries (see below)

### Arduino IDE Configuration

1. **Install ESP32 Board Package**
   - File → Preferences
   - Add to Additional Board Manager URLs:
     ```
     https://dl.espressif.com/dl/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager
   - Search "ESP32" and install

2. **Board Settings**
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → Select your COM port
   - Tools → Upload Speed → 921600
   - Tools → CPU Frequency → 240MHz (WiFi/BT)

3. **Serial Monitor**
   - Baud Rate: 115200

### Required Libraries

Install via Tools → Manage Libraries:

1. **Adafruit Unified Sensor** (by Adafruit)
2. **Adafruit BNO055** (by Adafruit)

### Hardware Wiring

```
BNO055 IMU → ESP32:
VIN  → 3.3V
GND  → GND
SDA  → GPIO21
SCL  → GPIO22

FSR Sensors → ESP32:
FSR_LEFT  → GPIO35 (with pull-down resistor)
FSR_RIGHT → GPIO34 (with pull-down resistor)

Vibration Motors → ESP32:
MOTOR1 → GPIO25 (with transistor driver)
MOTOR2 → GPIO26 (with transistor driver)
```

**Important Notes:**
- Use 3.3V for BNO055 (NOT 5V)
- Add 10kΩ pull-down resistors for FSR sensors
- Use transistor drivers for vibration motors
- USB power sufficient for testing

## Building and Uploading

1. **Open the sketch**
   ```
   File → Open → firmware/IMU_ESP32_config.ino
   ```

2. **Verify compilation**
   ```
   Sketch → Verify/Compile (Ctrl+R)
   ```

3. **Upload to ESP32**
   ```
   Sketch → Upload (Ctrl+U)
   ```

4. **Monitor serial output**
   ```
   Tools → Serial Monitor (Ctrl+Shift+M)
   Set baud rate to 115200
   ```

## Current Functionality

### Sensor Reading
- IMU orientation data (pitch, roll, yaw)
- FSR pressure values with filtering
- 10Hz sampling rate with 100ms delay

### Data Processing
- Low-pass filtering for stable sensor readings
- Real-time posture analysis
- Threshold-based feedback triggering

### Feedback System
- Test vibration motor activation after 5 seconds
- Configurable feedback intensity and duration
- Safety timeouts to prevent overstimulation

## Planned Enhancements

### Advanced Features
- WiFi connectivity for data transmission
- Battery level monitoring
- Sleep mode for power conservation
- Over-the-air (OTA) firmware updates

### Clinical Features
- Patient-specific calibration
- Adaptive threshold adjustment
- Data logging to SD card
- Bluetooth connectivity option

### Safety Features
- Watchdog timer implementation
- Sensor failure detection
- Emergency shutdown capability
- Temperature monitoring

## Development Guidelines

### Code Structure
- Clear pin definitions at top of file
- Modular functions for different subsystems
- Comprehensive error handling
- Detailed serial output for debugging

### Performance Optimization
- Minimize power consumption for battery operation
- Optimize sensor reading frequency
- Efficient data processing algorithms
- Memory management for continuous operation

### Medical Device Considerations
- **Safety**: Fail-safe mechanisms for patient protection
- **Reliability**: Robust operation in clinical environments
- **Calibration**: Patient-specific threshold configuration
- **Validation**: Comprehensive testing protocols
- **Compliance**: Medical device development standards

## Debugging

### Serial Monitor Output
```
Starting ESP32 + BNO055...
BNO055 OK
Pitch: 2.34 | FSR L: 1024 | FSR R: 987
MOTOR1 ON
```

### Common Issues
1. **BNO055 NOT DETECTED**: Check I2C wiring (SDA/SCL)
2. **Erratic sensor readings**: Add proper filtering
3. **Motor not activating**: Check transistor drivers
4. **Power issues**: Ensure adequate current supply

### Testing Procedures
1. Verify sensor initialization
2. Check baseline sensor readings
3. Test motor activation
4. Validate threshold detection
5. Monitor continuous operation

## Contributing

1. Follow Arduino coding standards
2. Use descriptive variable names
3. Add comprehensive comments
4. Test on actual hardware
5. Document any hardware modifications
6. Consider power consumption in all changes

## Safety Warnings

- **Medical Use**: This is research/development code - not for clinical use without validation
- **Power**: Do not exceed component voltage ratings
- **Testing**: Always test with qualified personnel present
- **Modifications**: Document all hardware changes for safety review