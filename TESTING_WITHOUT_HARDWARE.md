# Testing ESP32 Integration Without Hardware

This guide shows you how to test the complete ESP32 integration system without needing physical Arduino hardware.

## Quick Start (3 Steps)

### 1. Start the Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 2. Start the Frontend (Optional)
```bash
cd frontend
npm install
npm start
```

### 3. Run the Hardware-less Test
```bash
cd backend
python test_without_hardware.py
```

## Testing Options

### Option 1: Automated Testing Suite
The easiest way - runs all tests automatically:

```bash
cd backend
python test_without_hardware.py
```

This will test:
- ✅ Backend API endpoints
- ✅ Sensor data processing with simulated data
- ✅ WebSocket real-time connections
- ✅ Clinical algorithms with test scenarios
- ✅ Frontend integration (if running)
- ✅ 30-second ESP32 simulation

### Option 2: Manual ESP32 Simulation
Simulate a real ESP32 device sending data:

```bash
cd backend
python esp32_simulator.py --scenario mild_pusher --interval 0.5
```

**Available scenarios:**
- `normal` - Normal posture patterns
- `mild_pusher` - Mild pusher syndrome symptoms
- `severe_pusher` - Severe pusher syndrome patterns

**Options:**
- `--device-id ESP32_SIM_001` - Set device ID
- `--interval 0.2` - Set transmission interval (seconds)
- `--calibrate` - Run calibration simulation first
- `--backend-url http://localhost:8000` - Backend URL

### Option 3: Demo Mode Testing
Use the built-in demo mode:

```bash
# Enable demo mode
curl -X POST http://localhost:8000/api/demo/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "scenario": "pusher_syndrome"}'

# Check demo status
curl http://localhost:8000/api/demo/status

# Disable demo mode
curl -X POST http://localhost:8000/api/demo/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Option 4: Manual API Testing
Test individual endpoints with curl:

```bash
# Test sensor data endpoint
curl -X POST http://localhost:8000/api/sensor-data \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: ESP32_TEST_001" \
  -H "X-Device-Signature: test_signature" \
  -H "X-Timestamp: $(date +%s)" \
  -d '{
    "deviceId": "ESP32_TEST_001",
    "timestamp": '$(date +%s000)',
    "pitch": 15.0,
    "roll": 2.0,
    "yaw": 0.5,
    "fsrLeft": 1600,
    "fsrRight": 2400
  }'
```

## What You'll See

### 1. Normal Posture Detection
```
🟢 NORMAL | Pitch: +2.50° | FSR: 2048/2048 | Score: 0
```

### 2. Pusher Syndrome Detection
```
🔴 PUSHER | Pitch: +15.00° | FSR: 1600/2400 | Score: 2
```

### 3. Real-time WebSocket Updates
The frontend will show live updates as the simulator sends data.

### 4. Clinical Analysis
Each sensor reading gets analyzed for:
- Pusher syndrome detection
- Clinical scoring (0-3 scale)
- Tilt classification (normal/pusher-relevant/severe)
- Weight distribution analysis

## Frontend Testing

If you have the frontend running (`npm start`), you can:

1. **Open http://localhost:3000**
2. **Navigate to the monitoring page**
3. **Enable demo mode** or **run the simulator**
4. **Watch real-time updates** in the dashboard

### Key Components to Test:
- **PostureVisualization** - Shows body lean direction
- **CircularTiltMeter** - Displays tilt angles
- **SensorDataDisplay** - Shows FSR values and connection status
- **AlertMessage** - Displays pusher syndrome alerts
- **CalibrationUI** - Test calibration workflow

## Advanced Testing

### Run Property-Based Tests
```bash
cd backend
python test_clinical_pusher_detection_property.py
python test_system_performance_under_load_property.py
python test_security_and_privacy_protection_property.py
```

### Run End-to-End Integration Tests
```bash
cd backend
python test_end_to_end_integration.py
```

### Run Performance Tests
```bash
cd backend
python test_performance_and_load.py
```

### Run Final System Validation
```bash
cd backend
python final_system_validation.py
```

## Calibration Testing

Test the calibration workflow without hardware:

```bash
# Run calibration simulation
cd backend
python esp32_simulator.py --calibrate --scenario normal

# Or test calibration API directly
curl -X POST http://localhost:8000/api/calibration/start \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "ESP32_TEST_001",
    "patientId": "test_patient",
    "duration": 30
  }'
```

## Multiple Device Testing

Simulate multiple ESP32 devices:

```bash
# Terminal 1
python esp32_simulator.py --device-id ESP32_SIM_001 --scenario normal

# Terminal 2  
python esp32_simulator.py --device-id ESP32_SIM_002 --scenario mild_pusher

# Terminal 3
python esp32_simulator.py --device-id ESP32_SIM_003 --scenario severe_pusher
```

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is in use
netstat -an | findstr :8000

# Try different port
uvicorn main:app --reload --port 8001
```

### Frontend Not Connecting
- Check that backend is running on port 8000
- Verify CORS settings in backend
- Check browser console for errors

### Simulator Connection Issues
- Verify backend URL is correct
- Check firewall settings
- Ensure backend is accepting connections

### WebSocket Issues
- Check if WebSocket endpoint is accessible
- Verify browser supports WebSockets
- Check for proxy/firewall blocking WebSocket connections

## Expected Test Results

When everything is working correctly, you should see:

✅ **Backend API**: All endpoints responding  
✅ **Sensor Processing**: Correct pusher syndrome detection  
✅ **WebSocket**: Real-time data streaming  
✅ **Clinical Algorithms**: Accurate clinical scoring  
✅ **Frontend**: Live dashboard updates  
✅ **Simulation**: Realistic ESP32 behavior  

## Next Steps

Once testing is complete without hardware:

1. **Deploy to staging environment**
2. **Test with real ESP32 hardware** (when available)
3. **Conduct clinical validation** with healthcare professionals
4. **Performance testing** under real-world conditions
5. **Security audit** for medical device compliance

## Support

If you encounter issues:

1. Check the console output for error messages
2. Verify all dependencies are installed
3. Ensure backend and frontend are running
4. Check network connectivity
5. Review the logs for detailed error information

The system is designed to work completely without hardware, so you can develop, test, and demonstrate the full ESP32 integration using only simulation and demo modes!