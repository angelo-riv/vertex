# Backend - Clinical Data Processing Server

FastAPI-based backend server for processing sensor data from the wearable device and providing clinical analytics for therapists.

## Overview

The backend handles:
- Real-time sensor data processing from ESP32 device
- Patient data storage and management
- Clinical analytics and progress tracking
- API endpoints for therapist dashboard
- Data logging for rehabilitation analysis

## Technology Stack

- **Framework**: FastAPI 0.129.0
- **Server**: Uvicorn 0.40.0
- **Data Validation**: Pydantic 2.12.5
- **Python**: 3.8+

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Server

**Development Mode**
```bash
uvicorn main:app --reload
```

**Production Mode**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`

## API Endpoints

### Current Endpoints
- `GET /` - Health check
- `GET /api/data` - Sample data endpoint

### Planned Endpoints
- `POST /api/sensor-data` - Receive sensor data from ESP32
- `GET /api/patients` - Patient management
- `GET /api/sessions` - Therapy session data
- `GET /api/analytics` - Clinical analytics and progress reports

## Development

### Project Structure
```
backend/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── venv/               # Virtual environment (local)
└── README.md           # This file
```

### Adding New Features

1. **API Routes**: Add new endpoints in `main.py` or separate route modules
2. **Data Models**: Use Pydantic models for request/response validation
3. **Database**: Plan to integrate database for patient data storage
4. **Real-time**: Consider WebSocket connections for live sensor data

### CORS Configuration

The server is configured to accept requests from:
- `http://localhost:3000` (React development server)
- `http://localhost:5173` (Alternative React dev server)

### Medical Device Considerations

- **Data Privacy**: Implement proper patient data protection
- **Real-time Processing**: Optimize for sub-100ms sensor data processing
- **Reliability**: Add error handling and failsafe mechanisms
- **Logging**: Comprehensive audit trails for clinical use
- **Validation**: Strict data validation for medical accuracy

## Testing

```bash
# Run tests (when implemented)
pytest

# API testing
# Use tools like Postman or curl to test endpoints
curl http://localhost:8000/api/data
```

## Deployment

For production deployment, consider:
- Database integration (PostgreSQL recommended for medical data)
- Authentication and authorization
- HTTPS/SSL certificates
- Load balancing for multiple devices
- Backup and disaster recovery
- Compliance with medical data regulations (HIPAA, etc.)

## Contributing

1. Follow Python PEP 8 style guidelines
2. Use type hints for all functions
3. Add comprehensive error handling
4. Document all API endpoints
5. Write tests for new functionality