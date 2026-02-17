# Vertex - Pusher Syndrome Rehabilitation Device

A wearable rehabilitation system designed to assist stroke patients with Pusher Syndrome through real-time posture correction and clinical monitoring.

## About Pusher Syndrome

Pusher Syndrome is a neurological condition commonly seen after stroke where patients experience altered perception of body orientation. This causes them to actively push away from their unaffected side and lean toward their affected side, creating asymmetrical posture that impairs balance, mobility, and recovery.

## System Overview

Our rehabilitation device consists of:

- **Wearable Hardware**: Chest-strap mounted ESP32 device with IMU and pressure sensors
- **Real-time Feedback**: Vibration motors provide immediate corrective haptic feedback
- **Clinical Dashboard**: Web interface for therapists to monitor patient progress
- **Data Analytics**: Comprehensive logging and visualization of posture patterns

## Key Benefits

- **Continuous Correction**: 24/7 posture monitoring and feedback outside clinical settings
- **Neuroplastic Retraining**: Supports brain retraining through consistent haptic cues
- **Clinical Insights**: Objective data for therapy optimization and progress tracking
- **Cost-Effective**: Low-cost alternative to expensive clinical rehabilitation equipment
- **Portable**: Enables rehabilitation in home and community environments

## Quick Start

### Prerequisites
- Arduino IDE (for firmware)
- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)

### Build Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vertex
   ```

2. **Set up each component** (see individual README files for detailed instructions):
   - [Backend Setup](backend/README.md) - FastAPI server and data processing
   - [Frontend Setup](frontend/README.md) - React clinical dashboard
   - [Firmware Setup](firmware/README.md) - ESP32 wearable device

3. **Development workflow**:
   - Upload firmware to ESP32 device
   - Start backend server: `cd backend && uvicorn main:app --reload`
   - Start frontend dashboard: `cd frontend && npm start`

## Project Structure

```
/
├── backend/     # FastAPI server for data processing and API
├── frontend/    # React web dashboard for therapists
├── firmware/    # ESP32 Arduino code for wearable device
└── .kiro/       # Development configuration and steering
```

## Clinical Applications

- **Stroke Rehabilitation**: Primary treatment for Pusher Syndrome patients
- **Physical Therapy**: Integration with existing physiotherapy protocols
- **Home Care**: Continuous monitoring outside clinical environments
- **Progress Tracking**: Objective measurement of recovery trends

## Development Status

This is an active research and development project. The system is designed for clinical research and should not be used as a medical device without proper validation and regulatory approval.

## Contributing

Please read the individual README files in each subdirectory for component-specific development guidelines and setup instructions.
