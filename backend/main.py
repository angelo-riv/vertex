from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from root directory
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

app = FastAPI(title="Vertex Rehabilitation API", version="1.0.0")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-key")

# Debug: Print to verify environment variables are loaded (remove in production)
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {'***' + SUPABASE_KEY[-10:] if SUPABASE_KEY else 'NOT SET'}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Allow frontend React app to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for data validation
class PatientProfile(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    age: Optional[int] = None
    stroke_side: Optional[str] = None
    severity_level: Optional[int] = None
    mobility_level: Optional[str] = None
    stroke_timeline: Optional[int] = None
    therapy_status: Optional[str] = None
    notifications_enabled: bool = True

class SensorReading(BaseModel):
    device_id: str
    timestamp: datetime
    imu_pitch: float
    imu_roll: float
    imu_yaw: float
    fsr_left: float
    fsr_right: float

class PostureStatus(BaseModel):
    tilt_angle: float
    tilt_direction: str
    alert_level: str  # "safe", "warning", "unsafe"
    fsr_balance: float
    haptic_active: bool

class MonitoringSession(BaseModel):
    id: Optional[str] = None
    patient_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    upright_percentage: Optional[float] = None
    average_tilt: Optional[float] = None
    correction_count: Optional[int] = 0

class CalibrationData(BaseModel):
    patient_id: str
    baseline_pitch: float
    baseline_roll: float
    warning_threshold: float
    danger_threshold: float

# Helper functions
def calculate_tilt_angle(pitch: float, roll: float) -> float:
    """Calculate tilt angle from IMU pitch and roll"""
    import math
    return math.sqrt(pitch**2 + roll**2)

def calculate_balance(fsr_left: float, fsr_right: float) -> float:
    """Calculate balance from FSR readings (-1 to 1, left to right bias)"""
    total = fsr_left + fsr_right
    if total == 0:
        return 0
    return (fsr_right - fsr_left) / total

def assess_alert_level(tilt_angle: float, balance: float, thresholds: dict) -> str:
    """Assess alert level based on tilt and balance"""
    if tilt_angle > thresholds.get('danger_threshold', 15.0):
        return 'unsafe'
    elif tilt_angle > thresholds.get('warning_threshold', 8.0):
        return 'warning'
    else:
        return 'safe'

# API Routes
@app.get("/")
def read_root():
    return {"message": "Vertex Rehabilitation API", "version": "1.0.0"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Patient Management Endpoints
@app.post("/api/patients", response_model=PatientProfile)
async def create_patient(patient: PatientProfile):
    try:
        result = supabase.table("patients").insert(patient.dict(exclude_unset=True)).execute()
        if result.data:
            return PatientProfile(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create patient")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/patients/{patient_id}", response_model=PatientProfile)
async def get_patient(patient_id: str):
    try:
        result = supabase.table("patients").select("*").eq("id", patient_id).execute()
        if result.data:
            return PatientProfile(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="Patient not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/patients/{patient_id}", response_model=PatientProfile)
async def update_patient(patient_id: str, updates: dict):
    try:
        result = supabase.table("patients").update(updates).eq("id", patient_id).execute()
        if result.data:
            return PatientProfile(**result.data[0])
        else:
            raise HTTPException(status_code=404, detail="Patient not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Device Communication Endpoints
@app.post("/api/device/sensor-data")
async def receive_sensor_data(patient_id: str, sensor_data: SensorReading):
    try:
        # Store raw sensor data
        data_to_insert = sensor_data.dict()
        data_to_insert['patient_id'] = patient_id
        
        result = supabase.table("sensor_readings").insert(data_to_insert).execute()
        
        # Process sensor data for real-time status
        tilt_angle = calculate_tilt_angle(sensor_data.imu_pitch, sensor_data.imu_roll)
        balance = calculate_balance(sensor_data.fsr_left, sensor_data.fsr_right)
        
        # Get patient thresholds (simplified for now)
        thresholds = {'warning_threshold': 8.0, 'danger_threshold': 15.0}
        alert_level = assess_alert_level(tilt_angle, balance, thresholds)
        
        # Determine tilt direction
        if abs(sensor_data.imu_roll) > abs(sensor_data.imu_pitch):
            tilt_direction = 'left' if sensor_data.imu_roll < 0 else 'right'
        else:
            tilt_direction = 'forward' if sensor_data.imu_pitch > 0 else 'backward'
        
        posture_status = PostureStatus(
            tilt_angle=tilt_angle,
            tilt_direction=tilt_direction,
            alert_level=alert_level,
            fsr_balance=balance,
            haptic_active=alert_level != 'safe'
        )
        
        return {"status": "success", "posture_status": posture_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/current/{patient_id}", response_model=PostureStatus)
async def get_current_posture(patient_id: str):
    try:
        # Get most recent sensor reading
        result = supabase.table("sensor_readings")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No sensor data found")
        
        reading = result.data[0]
        tilt_angle = calculate_tilt_angle(reading['imu_pitch'], reading['imu_roll'])
        balance = calculate_balance(reading['fsr_left'], reading['fsr_right'])
        
        # Get patient thresholds
        thresholds = {'warning_threshold': 8.0, 'danger_threshold': 15.0}
        alert_level = assess_alert_level(tilt_angle, balance, thresholds)
        
        # Determine tilt direction
        if abs(reading['imu_roll']) > abs(reading['imu_pitch']):
            tilt_direction = 'left' if reading['imu_roll'] < 0 else 'right'
        else:
            tilt_direction = 'forward' if reading['imu_pitch'] > 0 else 'backward'
        
        return PostureStatus(
            tilt_angle=tilt_angle,
            tilt_direction=tilt_direction,
            alert_level=alert_level,
            fsr_balance=balance,
            haptic_active=alert_level != 'safe'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@app.post("/api/monitoring/start", response_model=MonitoringSession)
async def start_monitoring_session(patient_id: str):
    try:
        session_data = {
            "patient_id": patient_id,
            "start_time": datetime.now().isoformat()
        }
        
        result = supabase.table("monitoring_sessions").insert(session_data).execute()
        if result.data:
            return MonitoringSession(**result.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to start session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/stop/{session_id}")
async def stop_monitoring_session(session_id: str, session_summary: dict):
    try:
        update_data = {
            "end_time": datetime.now().isoformat(),
            "duration_minutes": session_summary.get("duration_minutes"),
            "upright_percentage": session_summary.get("upright_percentage"),
            "average_tilt": session_summary.get("average_tilt"),
            "correction_count": session_summary.get("correction_count", 0)
        }
        
        result = supabase.table("monitoring_sessions")\
            .update(update_data)\
            .eq("id", session_id)\
            .execute()
        
        return {"status": "success", "message": "Session ended successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Calibration Endpoints
@app.post("/api/device/calibrate")
async def save_calibration(calibration: CalibrationData):
    try:
        # Deactivate previous calibrations
        supabase.table("device_calibrations")\
            .update({"is_active": False})\
            .eq("patient_id", calibration.patient_id)\
            .execute()
        
        # Insert new calibration
        calibration_data = calibration.dict()
        calibration_data["calibration_date"] = datetime.now().isoformat()
        calibration_data["is_active"] = True
        
        result = supabase.table("device_calibrations").insert(calibration_data).execute()
        
        return {"status": "success", "message": "Calibration saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/device/calibration/{patient_id}")
async def get_active_calibration(patient_id: str):
    try:
        result = supabase.table("device_calibrations")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .order("calibration_date", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(status_code=404, detail="No active calibration found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics/sessions/{patient_id}")
async def get_session_history(patient_id: str, limit: int = 50):
    try:
        result = supabase.table("monitoring_sessions")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("start_time", desc=True)\
            .limit(limit)\
            .execute()
        
        return {"sessions": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/summary/{patient_id}")
async def get_analytics_summary(patient_id: str):
    try:
        # Get recent sessions for summary
        sessions_result = supabase.table("monitoring_sessions")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("start_time", desc=True)\
            .limit(30)\
            .execute()
        
        sessions = sessions_result.data
        if not sessions:
            return {"message": "No session data available"}
        
        # Calculate summary statistics
        total_sessions = len(sessions)
        avg_upright = sum(s.get('upright_percentage', 0) for s in sessions) / total_sessions
        avg_duration = sum(s.get('duration_minutes', 0) for s in sessions) / total_sessions
        total_corrections = sum(s.get('correction_count', 0) for s in sessions)
        
        return {
            "total_sessions": total_sessions,
            "average_upright_percentage": round(avg_upright, 1),
            "average_session_duration": round(avg_duration, 1),
            "total_corrections": total_corrections,
            "improvement_trend": "stable"  # Simplified for now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))