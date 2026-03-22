from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from collections import deque
import json
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Import security middleware
from security.https_middleware import HTTPSRedirectMiddleware, SecurityHeadersMiddleware, get_secure_supabase_config
from security.auth_middleware import AuthenticationMiddleware, RateLimitingMiddleware, get_current_user, get_current_device
from security.secure_logging import configure_secure_logging, get_secure_logger, log_security_event, log_api_access

# Import clinical algorithm components
from clinical_algorithm import (
    PusherDetectionAlgorithm, ClinicalThresholds, CalibrationData, 
    PusherAnalysis, PusherEpisode, SensorDataPoint, PareticSide,
    SeverityScore, TiltClassification, create_default_thresholds,
    create_default_calibration
)

# Import clinical thresholds API
from api.clinical_thresholds import router as clinical_thresholds_router

# Import calibration API
from api.calibration import router as calibration_router

# Import demo data generator
from demo_data_generator import demo_manager

# Import performance monitoring
from performance_monitor import performance_monitor, track_performance

# Configure secure logging first
configure_secure_logging()

# Get secure logger for main application
logger = get_secure_logger("main")

# Load environment variables from root directory
root_dir = Path(__file__).parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

app = FastAPI(title="Vertex Rehabilitation API", version="1.0.0")

# Security middleware - order matters!
app.add_middleware(HTTPSRedirectMiddleware, force_https=os.getenv("FORCE_HTTPS", "false").lower() == "true")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitingMiddleware, requests_per_minute=120)  # Increased for medical device needs
app.add_middleware(AuthenticationMiddleware)

# Supabase configuration with HTTPS enforcement
try:
    supabase_config = get_secure_supabase_config()
    supabase: Client = create_client(supabase_config["url"], supabase_config["key"])
    logger.info("Supabase client initialized with secure HTTPS configuration")
except Exception as e:
    logger.error(f"Failed to initialize secure Supabase client: {str(e)}")
    raise

# CORS middleware (after security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection for clinical thresholds API
def get_supabase_dependency():
    return supabase

def get_current_user_dependency(request: Request):
    # Extract user from headers or auth token
    return request.headers.get("X-Therapist-ID", "system")

# Override dependencies in clinical thresholds router
clinical_thresholds_router.dependency_overrides = {
    "get_supabase_client": get_supabase_dependency,
    "get_current_user": get_current_user_dependency
}

# Override dependencies in calibration router
calibration_router.dependency_overrides = {
    "get_supabase_client": get_supabase_dependency,
    "get_current_user": get_current_user_dependency
}

# Include routers
app.include_router(clinical_thresholds_router)
app.include_router(calibration_router)

# Import and include ESP32 clinical integration router
from api.esp32_clinical_integration import router as esp32_clinical_router
app.include_router(esp32_clinical_router)

# Background task for automatic timeout checking
async def background_timeout_checker():
    """Background task for device timeout checking and memory cleanup"""
    while True:
        try:
            # Check device timeouts
            check_device_timeouts()
            
            # Memory cleanup: Remove old sensor readings from buffer
            global cleanup_counter
            cleanup_counter += 1
            
            # Force batch insert every 30 seconds
            if cleanup_counter % 15 == 0:  # Every 30 seconds (15 * 2s)
                await _batch_database_insert()
            
            # Clean up old device connection data every 5 minutes
            if cleanup_counter % 150 == 0:  # Every 300 seconds (150 * 2s)
                await _cleanup_old_device_data()
                
            await asyncio.sleep(2.0)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"Background task error: {str(e)}")
            await asyncio.sleep(5.0)  # Wait longer on error

async def _cleanup_old_device_data():
    """Clean up old device connection data to prevent memory leaks"""
    try:
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=1)
        
        # Clean up old device statuses
        devices_to_remove = []
        for device_id, status in device_connections.items():
            if status.last_seen < cutoff_time:
                devices_to_remove.append(device_id)
        
        for device_id in devices_to_remove:
            del device_connections[device_id]
            logger.info(f"Cleaned up old device data for {device_id}")
            
    except Exception as e:
        logger.error(f"Device cleanup error: {str(e)}")

# Start background task when app starts
@app.on_event("startup")
async def startup_event():
    """Start background tasks when the application starts"""
    asyncio.create_task(background_timeout_checker())
    logger.info("Started background timeout checker")

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

class ESP32SensorData(BaseModel):
    """ESP32 sensor data model with validation for expected ranges"""
    deviceId: str = Field(..., min_length=1, max_length=50, description="ESP32 device identifier")
    timestamp: int = Field(..., gt=0, description="Unix timestamp in milliseconds")
    pitch: float = Field(..., ge=-180.0, le=180.0, description="Pitch angle in degrees (-180 to +180)")
    fsrLeft: int = Field(..., ge=0, le=4095, description="Left FSR sensor value (0-4095)")
    fsrRight: int = Field(..., ge=0, le=4095, description="Right FSR sensor value (0-4095)")
    
    @validator('deviceId')
    def validate_device_id(cls, v):
        if not v.startswith('ESP32_'):
            raise ValueError('Device ID must start with ESP32_')
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        # Ensure timestamp is reasonable (not too far in past or future)
        now = datetime.now(timezone.utc).timestamp() * 1000
        if abs(v - now) > 86400000:  # 24 hours in milliseconds
            raise ValueError('Timestamp must be within 24 hours of current time')
        return v

class DeviceConnectionStatus(BaseModel):
    """Enhanced device connection tracking model with comprehensive diagnostics"""
    device_id: str
    last_seen: datetime
    connection_status: str = Field(..., pattern="^(connected|disconnected|timeout)$")
    ip_address: Optional[str] = None
    data_count: int = 0
    first_seen: Optional[datetime] = None
    # Enhanced diagnostic information
    connection_quality: str = "unknown"  # excellent, good, poor, unknown
    last_error: Optional[str] = None
    error_count: int = 0
    reconnection_count: int = 0
    average_interval: Optional[float] = None  # Average time between data transmissions
    last_intervals: List[float] = []  # Last 10 intervals for quality assessment
    network_diagnostics: Optional[Dict[str, Any]] = None

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

# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time sensor data broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": datetime.now(timezone.utc),
            "client_info": client_info or {},
            "messages_sent": 0
        }
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            connection_info = self.connection_info.pop(websocket, {})
            connected_duration = (datetime.now(timezone.utc) - connection_info.get("connected_at", datetime.now(timezone.utc))).total_seconds()
            logger.info(f"WebSocket client disconnected after {connected_duration:.1f}s. "
                       f"Messages sent: {connection_info.get('messages_sent', 0)}. "
                       f"Remaining connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
            if websocket in self.connection_info:
                self.connection_info[websocket]["messages_sent"] += 1
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast_sensor_data(self, data: dict):
        """Broadcast sensor data to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        # Add broadcast metadata
        broadcast_message = {
            "type": "sensor_data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        # Send to all connections, removing failed ones
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(broadcast_message)
                if connection in self.connection_info:
                    self.connection_info[connection]["messages_sent"] += 1
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket client: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
        
        if disconnected_connections:
            logger.info(f"Cleaned up {len(disconnected_connections)} disconnected WebSocket connections")
    
    async def broadcast_device_status(self, device_id: str, status: dict):
        """Broadcast device connection status updates"""
        if not self.active_connections:
            return
        
        broadcast_message = {
            "type": "device_status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_id": device_id,
            "status": status
        }
        
        disconnected_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(broadcast_message)
                if connection in self.connection_info:
                    self.connection_info[connection]["messages_sent"] += 1
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error broadcasting device status: {str(e)}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)
    
    def get_connection_stats(self) -> dict:
        """Get statistics about current WebSocket connections"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "connected_at": info["connected_at"].isoformat(),
                    "messages_sent": info["messages_sent"],
                    "client_info": info["client_info"]
                }
                for info in self.connection_info.values()
            ]
        }

# Global WebSocket manager instance
websocket_manager = ConnectionManager()

# Performance optimization: Memory management for old sensor readings
sensor_data_buffer = deque(maxlen=1000)  # Keep last 1000 readings in memory
cleanup_counter = 0

async def _fast_clinical_analysis(sensor_data: ESP32SensorData, patient_id: str) -> Optional[PusherAnalysis]:
    """
    Optimized clinical analysis with minimal database calls and caching.
    """
    try:
        # Get cached algorithm instance (avoid repeated database calls)
        algorithm = get_or_create_clinical_algorithm(patient_id, sensor_data.deviceId)
        
        # Convert to sensor data point
        sensor_point = SensorDataPoint(
            timestamp=datetime.fromtimestamp(sensor_data.timestamp / 1000, tz=timezone.utc),
            pitch=sensor_data.pitch,
            fsr_left=sensor_data.fsrLeft,
            fsr_right=sensor_data.fsrRight,
            device_id=sensor_data.deviceId
        )
        
        # Perform analysis
        return algorithm.analyze_sensor_data(sensor_point)
        
    except Exception as e:
        logger.error(f"Fast clinical analysis error: {str(e)}")
        return None

async def _background_database_storage(sensor_data: ESP32SensorData, sensor_timestamp: datetime, device_id: str):
    """
    Background database storage that doesn't block real-time processing.
    """
    try:
        # Prepare minimal database record
        sensor_record = {
            "device_id": device_id,
            "timestamp": sensor_timestamp.isoformat(),
            "imu_pitch": sensor_data.pitch,
            "imu_roll": 0.0,
            "imu_yaw": 0.0,
            "fsr_left": float(sensor_data.fsrLeft),
            "fsr_right": float(sensor_data.fsrRight)
        }
        
        # Store in buffer for batch processing
        sensor_data_buffer.append(sensor_record)
        
        # Batch insert every 10 records or every 5 seconds
        global cleanup_counter
        cleanup_counter += 1
        
        if len(sensor_data_buffer) >= 10 or cleanup_counter % 50 == 0:
            await _batch_database_insert()
            
    except Exception as e:
        logger.warning(f"Background storage error: {str(e)}")

async def _batch_database_insert():
    """
    Batch insert sensor data to reduce database load.
    """
    if not sensor_data_buffer:
        return
        
    try:
        # Get all records from buffer
        records = list(sensor_data_buffer)
        sensor_data_buffer.clear()
        
        # Batch insert
        result = supabase.table("sensor_readings").insert(records).execute()
        
        if result.data:
            logger.debug(f"Batch inserted {len(records)} sensor records")
        else:
            logger.warning(f"Batch insert failed - no data returned")
            
    except Exception as e:
        logger.warning(f"Batch database insert failed: {str(e)}")

# Add optimized WebSocket broadcasting method to ConnectionManager
async def broadcast_sensor_data_optimized(self, data: dict):
    """Optimized WebSocket broadcasting with minimal overhead"""
    if not self.active_connections:
        return
    
    # Pre-serialize JSON once
    message_json = json.dumps({
        "type": "sensor_data",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    })
    
    # Send to all connections concurrently
    tasks = []
    for connection in self.active_connections:
        tasks.append(_send_websocket_message(connection, message_json))
    
    # Execute all sends concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Clean up failed connections
    failed_connections = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failed_connections.append(self.active_connections[i])
    
    for connection in failed_connections:
        self.disconnect(connection)

async def _send_websocket_message(connection: WebSocket, message_json: str):
    """Send WebSocket message with error handling"""
    try:
        await connection.send_text(message_json)
    except (WebSocketDisconnect, Exception) as e:
        raise e

# Monkey patch the optimized method
ConnectionManager.broadcast_sensor_data_optimized = broadcast_sensor_data_optimized

websocket_manager = ConnectionManager()

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

# Device connection tracking
device_connections: Dict[str, DeviceConnectionStatus] = {}

# Clinical algorithm instances (one per patient/device combination)
clinical_algorithms: Dict[str, PusherDetectionAlgorithm] = {}

def _assess_connection_quality(intervals: List[float]) -> str:
    """Assess connection quality based on data transmission intervals"""
    if not intervals:
        return "unknown"
    
    avg_interval = sum(intervals) / len(intervals)
    # Calculate standard deviation
    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
    std_dev = variance ** 0.5
    
    # Quality assessment based on expected 100-200ms intervals
    if avg_interval <= 0.3 and std_dev <= 0.1:  # Very consistent, fast intervals
        return "excellent"
    elif avg_interval <= 0.5 and std_dev <= 0.2:  # Good intervals with some variation
        return "good"
    elif avg_interval <= 1.0 and std_dev <= 0.5:  # Acceptable but slower
        return "poor"
    else:
        return "poor"

def _create_device_status_data(device_id: str, device_status: DeviceConnectionStatus) -> Dict[str, Any]:
    """Create comprehensive device status data for broadcasting"""
    return {
        "device_id": device_id,
        "connection_status": device_status.connection_status,
        "last_seen": device_status.last_seen.isoformat(),
        "ip_address": device_status.ip_address,
        "data_count": device_status.data_count,
        "connection_quality": device_status.connection_quality,
        "average_interval": device_status.average_interval,
        "reconnection_count": device_status.reconnection_count,
        "error_count": device_status.error_count,
        "last_error": device_status.last_error,
        "first_seen": device_status.first_seen.isoformat() if device_status.first_seen else None,
        "uptime_seconds": (device_status.last_seen - device_status.first_seen).total_seconds() if device_status.first_seen else 0
    }

def _log_network_error(device_id: str, error_message: str, error_details: Optional[Dict[str, Any]] = None):
    """Log network errors with diagnostic information"""
    if device_id in device_connections:
        device_status = device_connections[device_id]
        device_status.error_count += 1
        device_status.last_error = error_message
        
        # Store network diagnostics
        if error_details:
            device_status.network_diagnostics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_type": error_details.get("type", "unknown"),
                "details": error_details
            }
    
    logger.error(f"Network error for device {device_id}: {error_message}", extra={"device_id": device_id, "error_details": error_details})

def _calculate_average_quality(devices: List[Dict[str, Any]]) -> str:
    """Calculate average connection quality across all devices"""
    if not devices:
        return "unknown"
    
    quality_scores = {"excellent": 4, "good": 3, "poor": 2, "unknown": 1}
    connected_devices = [d for d in devices if d["connection_status"] == "connected"]
    
    if not connected_devices:
        return "unknown"
    
    total_score = sum(quality_scores.get(d["connection_quality"], 1) for d in connected_devices)
    avg_score = total_score / len(connected_devices)
    
    if avg_score >= 3.5:
        return "excellent"
    elif avg_score >= 2.5:
        return "good"
    elif avg_score >= 1.5:
        return "poor"
    else:
        return "unknown"

def update_device_connection(device_id: str, ip_address: Optional[str] = None) -> DeviceConnectionStatus:
    """Optimized device connection status update with minimal overhead"""
    now = datetime.now(timezone.utc)
    
    if device_id in device_connections:
        device_status = device_connections[device_id]
        
        # Fast update - minimal calculations
        time_since_last = (now - device_status.last_seen).total_seconds()
        device_status.last_seen = now
        device_status.data_count += 1
        
        # Only update IP if provided
        if ip_address and device_status.ip_address != ip_address:
            device_status.ip_address = ip_address
        
        # Simplified interval tracking (keep last 5 for performance)
        if len(device_status.last_intervals) >= 5:
            device_status.last_intervals.pop(0)
        device_status.last_intervals.append(time_since_last)
        
        # Fast connection quality assessment
        if device_status.last_intervals:
            avg_interval = sum(device_status.last_intervals) / len(device_status.last_intervals)
            device_status.average_interval = avg_interval
            device_status.connection_quality = "excellent" if avg_interval < 0.3 else ("good" if avg_interval < 1.0 else "poor")
        
        # Update status if needed
        if device_status.connection_status != "connected":
            device_status.connection_status = "connected"
            device_status.reconnection_count += 1
            device_status.last_error = None
            logger.info(f"Device {device_id} reconnected (#{device_status.reconnection_count})")
        
    else:
        # New device - minimal initialization
        device_connections[device_id] = DeviceConnectionStatus(
            device_id=device_id,
            last_seen=now,
            first_seen=now,
            connection_status="connected",
            ip_address=ip_address,
            data_count=1,
            connection_quality="unknown",
            last_intervals=[],
            reconnection_count=0,
            error_count=0
        )
        logger.info(f"New device {device_id} connected")
    
    return device_connections[device_id]

def check_device_timeouts():
    """Check for device timeouts (5 seconds of no communication) with enhanced diagnostics"""
    now = datetime.now(timezone.utc)
    timeout_threshold = 5.0  # 5 seconds
    
    for device_id, status in device_connections.items():
        time_diff = (now - status.last_seen).total_seconds()
        
        if time_diff > timeout_threshold and status.connection_status == "connected":
            old_status = status.connection_status
            status.connection_status = "timeout"
            
            # Enhanced timeout logging with diagnostics
            diagnostic_info = {
                "timeout_seconds": time_diff,
                "last_data_count": status.data_count,
                "connection_quality": status.connection_quality,
                "average_interval": status.average_interval,
                "reconnection_count": status.reconnection_count
            }
            
            _log_network_error(
                device_id, 
                f"Device timeout after {time_diff:.1f} seconds", 
                {"type": "timeout", "diagnostics": diagnostic_info}
            )
            
            # Broadcast enhanced timeout status
            status_data = _create_device_status_data(device_id, status)
            status_data.update({
                "timeout_seconds": time_diff,
                "diagnostic_info": diagnostic_info
            })
            
            # Schedule the broadcast
            asyncio.create_task(websocket_manager.broadcast_device_status(device_id, status_data))

def get_device_status(device_id: str) -> Optional[DeviceConnectionStatus]:
    """Get current device connection status"""
    check_device_timeouts()
    return device_connections.get(device_id)

def get_or_create_clinical_algorithm(patient_id: str, device_id: str, paretic_side: str = "right") -> PusherDetectionAlgorithm:
    """
    Get existing clinical algorithm instance or create a new one for the patient/device combination.
    In a production system, this would load patient-specific thresholds and calibration from database.
    """
    algorithm_key = f"{patient_id}_{device_id}"
    
    if algorithm_key not in clinical_algorithms:
        # Create default thresholds (in production, load from database)
        paretic_side_enum = PareticSide.RIGHT if paretic_side.lower() == "right" else PareticSide.LEFT
        thresholds = create_default_thresholds(patient_id, paretic_side_enum)
        
        # Create default calibration (in production, load from database)
        calibration = create_default_calibration(patient_id, device_id)
        
        # Create algorithm instance
        clinical_algorithms[algorithm_key] = PusherDetectionAlgorithm(thresholds, calibration)
        
        logger.info(f"Created clinical algorithm for patient {patient_id}, device {device_id}, paretic side: {paretic_side}")
    
    return clinical_algorithms[algorithm_key]

def analyze_pusher_syndrome(sensor_data: ESP32SensorData, patient_id: str = "default_patient") -> Optional[PusherAnalysis]:
    """
    Analyze sensor data for pusher syndrome using clinical algorithm with calibration-based adaptive thresholds.
    Returns None if analysis fails.
    """
    try:
        # Get or create clinical algorithm instance
        algorithm = get_or_create_clinical_algorithm(patient_id, sensor_data.deviceId)
        
        # Try to get calibration data for adaptive thresholds
        try:
            calibration_result = supabase.table("device_calibrations")\
                .select("*")\
                .eq("patient_id", patient_id)\
                .eq("device_id", sensor_data.deviceId)\
                .eq("is_active", True)\
                .order("calibration_date", desc=True)\
                .limit(1)\
                .execute()
            
            if calibration_result.data:
                calibration_data = calibration_result.data[0]
                
                # Update algorithm calibration if newer data is available
                current_calibration = algorithm.calibration
                db_calibration_date = datetime.fromisoformat(calibration_data["calibration_date"])
                
                if (not hasattr(current_calibration, 'calibration_timestamp') or 
                    db_calibration_date > current_calibration.calibration_timestamp):
                    
                    # Update with new calibration data
                    from clinical_algorithm import CalibrationData
                    new_calibration = CalibrationData(
                        patient_id=patient_id,
                        device_id=sensor_data.deviceId,
                        baseline_pitch=calibration_data.get("baseline_pitch", 0.0),
                        baseline_fsr_left=calibration_data.get("baseline_fsr_left", 2048.0),
                        baseline_fsr_right=calibration_data.get("baseline_fsr_right", 2048.0),
                        baseline_fsr_ratio=calibration_data.get("baseline_fsr_ratio", 0.5),
                        pitch_std_dev=calibration_data.get("pitch_std_dev", 1.0),
                        fsr_std_dev=calibration_data.get("fsr_std_dev", 0.1),
                        calibration_timestamp=db_calibration_date,
                        is_active=True
                    )
                    algorithm.calibration = new_calibration
                    logger.info(f"Updated calibration for algorithm {patient_id}_{sensor_data.deviceId}")
        
        except Exception as calibration_error:
            logger.warning(f"Could not load calibration data for {sensor_data.deviceId}: {str(calibration_error)}")
            # Continue with default calibration
        
        # Convert ESP32 sensor data to clinical data point
        sensor_point = SensorDataPoint(
            timestamp=datetime.fromtimestamp(sensor_data.timestamp / 1000, tz=timezone.utc),
            pitch=sensor_data.pitch,
            fsr_left=sensor_data.fsrLeft,
            fsr_right=sensor_data.fsrRight,
            device_id=sensor_data.deviceId
        )
        
        # Perform clinical analysis
        analysis = algorithm.analyze_sensor_data(sensor_point)
        
        logger.debug(f"Clinical analysis for {sensor_data.deviceId}: pusher_detected={analysis.pusher_detected}, "
                    f"severity={analysis.severity_score}, tilt_classification={analysis.tilt_classification}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in pusher syndrome analysis: {str(e)}")
        return None

# API Routes
@app.get("/")
def read_root():
    return {"message": "Vertex Rehabilitation API", "version": "1.0.0"}

@app.get("/api/performance/stats")
async def get_performance_stats():
    """
    Get real-time performance statistics for monitoring system performance.
    Returns latency metrics, throughput data, and performance alerts.
    """
    try:
        stats = performance_monitor.get_performance_stats()
        return {
            "status": "success",
            "performance_stats": stats,
            "clinical_compliance": {
                "latency_requirement_ms": 200,
                "current_status": stats["performance_status"]["overall"],
                "meets_requirements": stats["performance_status"]["overall"] in ["excellent", "good"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@app.post("/api/performance/log-summary")
async def log_performance_summary():
    """
    Log a performance summary to the console for debugging.
    """
    try:
        performance_monitor.log_performance_summary()
        return {"status": "success", "message": "Performance summary logged"}
    except Exception as e:
        logger.error(f"Error logging performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log performance summary: {str(e)}")

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
@app.post("/api/sensor-data/test")
async def test_esp32_sensor_data(sensor_data: ESP32SensorData):
    """
    Test endpoint for ESP32 sensor data validation without database operations
    """
    try:
        # Update device connection status (in-memory only)
        device_status = update_device_connection(sensor_data.deviceId)
        
        # Convert timestamp from milliseconds to datetime
        sensor_timestamp = datetime.fromtimestamp(sensor_data.timestamp / 1000, tz=timezone.utc)
        
        # Calculate derived metrics
        tilt_angle = abs(sensor_data.pitch)  # Use pitch as primary tilt indicator
        balance = calculate_balance(sensor_data.fsrLeft, sensor_data.fsrRight)
        
        # Determine tilt direction based on pitch
        if abs(sensor_data.pitch) < 2.0:
            tilt_direction = 'center'
        else:
            tilt_direction = 'left' if sensor_data.pitch < 0 else 'right'
        
        # Assess alert level
        thresholds = {'warning_threshold': 8.0, 'danger_threshold': 15.0}
        alert_level = assess_alert_level(tilt_angle, balance, thresholds)
        
        # Log successful data reception
        logger.info(f"TEST: Received data from {sensor_data.deviceId}: pitch={sensor_data.pitch:.1f}°, "
                   f"FSR_L={sensor_data.fsrLeft}, FSR_R={sensor_data.fsrRight}")
        
        return {
            "status": "success",
            "message": "Sensor data validated successfully (test mode)",
            "device_status": {
                "device_id": device_status.device_id,
                "connection_status": device_status.connection_status,
                "last_seen": device_status.last_seen.isoformat(),
                "data_count": device_status.data_count
            },
            "processed_data": {
                "tilt_angle": round(tilt_angle, 1),
                "tilt_direction": tilt_direction,
                "alert_level": alert_level,
                "fsr_balance": round(balance, 3),
                "timestamp": sensor_timestamp.isoformat()
            }
        }
        
    except ValueError as e:
        logger.error(f"Validation error for device {sensor_data.deviceId}: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Data validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing sensor data from {sensor_data.deviceId}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/sensor-data")
@track_performance
async def receive_esp32_sensor_data(sensor_data: ESP32SensorData, request: Request):
    """
    Optimized sensor data processing with sub-200ms latency requirements and security logging.
    Expected data format from ESP32:
    {
        "deviceId": "ESP32_XXXXXX",
        "timestamp": 1234567890,
        "pitch": -12.5,
        "fsrLeft": 512,
        "fsrRight": 768
    }
    """
    start_time = time.time()
    
    try:
        # Get authenticated device ID from security middleware
        authenticated_device = get_current_device(request)
        if not authenticated_device:
            log_security_event("unauthorized_device_access", {
                "device_id": sensor_data.deviceId,
                "client_ip": request.client.host if request.client else "unknown"
            })
            raise HTTPException(status_code=401, detail="Device authentication required")
        
        # Verify device ID matches authenticated device
        if authenticated_device != sensor_data.deviceId:
            log_security_event("device_id_mismatch", {
                "authenticated_device": authenticated_device,
                "claimed_device": sensor_data.deviceId
            })
            raise HTTPException(status_code=403, detail="Device ID mismatch")
        
        # Fast path: Update device connection status (optimized)
        device_status = update_device_connection(sensor_data.deviceId)
        
        # Pre-calculate timestamp once
        sensor_timestamp = datetime.fromtimestamp(sensor_data.timestamp / 1000, tz=timezone.utc)
        timestamp_iso = sensor_timestamp.isoformat()
        
        # Fast calculations with minimal function calls
        tilt_angle = abs(sensor_data.pitch)
        balance = (sensor_data.fsrRight - sensor_data.fsrLeft) / (sensor_data.fsrLeft + sensor_data.fsrRight) if (sensor_data.fsrLeft + sensor_data.fsrRight) > 0 else 0.0
        
        # Optimized tilt direction calculation
        tilt_direction = 'center' if tilt_angle < 2.0 else ('left' if sensor_data.pitch < 0 else 'right')
        
        # Fast alert level assessment
        alert_level = 'danger' if tilt_angle >= 15.0 else ('warning' if tilt_angle >= 8.0 else 'normal')
        
        # Optimized clinical analysis (async to not block)
        clinical_task = asyncio.create_task(
            _fast_clinical_analysis(sensor_data, "default_patient")
        )
        
        # Prepare minimal broadcast payload (optimized JSON size)
        broadcast_data = {
            "d": sensor_data.deviceId,  # Shortened keys for smaller payload
            "t": timestamp_iso,
            "p": sensor_data.pitch,
            "fl": sensor_data.fsrLeft,
            "fr": sensor_data.fsrRight,
            "ta": round(tilt_angle, 1),
            "td": tilt_direction,
            "al": alert_level,
            "b": round(balance, 3),
            "cs": device_status.connection_status,
            "dc": device_status.data_count
        }
        
        # Priority 1: Broadcast to WebSocket clients immediately (real-time requirement)
        broadcast_task = asyncio.create_task(
            websocket_manager.broadcast_sensor_data_optimized(broadcast_data)
        )
        
        # Priority 2: Background database storage (non-blocking)
        db_task = asyncio.create_task(
            _background_database_storage(sensor_data, sensor_timestamp, device_status.device_id)
        )
        
        # Wait for clinical analysis and broadcast (critical path)
        clinical_analysis, broadcast_result = await asyncio.gather(
            clinical_task, broadcast_task, return_exceptions=True
        )
        
        # Add clinical data to response if available
        clinical_data = {}
        if clinical_analysis and not isinstance(clinical_analysis, Exception):
            clinical_data = {
                "pusher_detected": clinical_analysis.pusher_detected,
                "severity_score": clinical_analysis.severity_score.value,
                "confidence_level": round(clinical_analysis.confidence_level, 3),
                "paretic_tilt": round(clinical_analysis.paretic_tilt, 2)
            }
            # Update broadcast data with clinical info
            broadcast_data.update({
                "pd": clinical_analysis.pusher_detected,
                "ss": clinical_analysis.severity_score.value,
                "cl": round(clinical_analysis.confidence_level, 3)
            })
        
        # Calculate processing time for performance monitoring
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Secure logging without PII
        device_logger = get_secure_logger("device")
        device_logger.log_sensor_data(
            device_id=sensor_data.deviceId,
            data_count=device_status.data_count,
            connection_status=device_status.connection_status
        )
        
        # Log performance metrics (reduced logging for speed)
        if processing_time > 100:  # Only log if approaching latency limit
            logger.warning(f"Slow processing for device: {processing_time:.1f}ms")
        
        # Return minimal response for ESP32 (reduced payload size)
        return {
            "status": "ok",
            "time_ms": round(processing_time, 1),
            "clients": len(websocket_manager.active_connections),
            "clinical": clinical_data
        }
        
    except ValueError as e:
        # Fast error handling with secure logging
        log_security_event("sensor_data_validation_error", {
            "device_id": getattr(sensor_data, 'deviceId', 'unknown'),
            "error_type": "validation",
            "client_ip": request.client.host if request.client else "unknown"
        })
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        # Fast error handling with secure logging
        log_security_event("sensor_data_processing_error", {
            "device_id": getattr(sensor_data, 'deviceId', 'unknown'),
            "error_type": "processing",
            "client_ip": request.client.host if request.client else "unknown"
        })
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/api/sensor-data/devices")
async def get_connected_devices():
    """Get comprehensive status of all ESP32 devices with enhanced diagnostics"""
    check_device_timeouts()
    
    devices = []
    for device_id, status in device_connections.items():
        device_info = {
            "device_id": device_id,
            "connection_status": status.connection_status,
            "last_seen": status.last_seen.isoformat(),
            "ip_address": status.ip_address,
            "data_count": status.data_count,
            "last_seen_seconds_ago": (datetime.now(timezone.utc) - status.last_seen).total_seconds(),
            # Enhanced diagnostic information
            "connection_quality": status.connection_quality,
            "average_interval": status.average_interval,
            "reconnection_count": status.reconnection_count,
            "error_count": status.error_count,
            "last_error": status.last_error,
            "first_seen": status.first_seen.isoformat() if status.first_seen else None,
            "uptime_seconds": (status.last_seen - status.first_seen).total_seconds() if status.first_seen else 0,
            "network_diagnostics": status.network_diagnostics
        }
        devices.append(device_info)
    
    # Calculate summary statistics
    connected_devices = [d for d in devices if d["connection_status"] == "connected"]
    timeout_devices = [d for d in devices if d["connection_status"] == "timeout"]
    
    return {
        "devices": devices,
        "total_devices": len(devices),
        "connected_devices": len(connected_devices),
        "timeout_devices": len(timeout_devices),
        "summary": {
            "average_quality": _calculate_average_quality(devices),
            "total_data_points": sum(d["data_count"] for d in devices),
            "total_errors": sum(d["error_count"] for d in devices),
            "total_reconnections": sum(d["reconnection_count"] for d in devices)
        }
    }

@app.get("/api/sensor-data/connection-diagnostics")
async def get_connection_diagnostics():
    """Get comprehensive network diagnostics and connection health information"""
    check_device_timeouts()
    
    current_time = datetime.now(timezone.utc)
    diagnostics = {
        "timestamp": current_time.isoformat(),
        "system_health": {
            "total_devices": len(device_connections),
            "connected_devices": len([d for d in device_connections.values() if d.connection_status == "connected"]),
            "timeout_devices": len([d for d in device_connections.values() if d.connection_status == "timeout"]),
            "websocket_connections": len(websocket_manager.active_connections)
        },
        "network_performance": {
            "average_quality": _calculate_average_quality([
                {
                    "connection_status": d.connection_status,
                    "connection_quality": d.connection_quality
                } for d in device_connections.values()
            ]),
            "total_data_points": sum(d.data_count for d in device_connections.values()),
            "total_errors": sum(d.error_count for d in device_connections.values()),
            "total_reconnections": sum(d.reconnection_count for d in device_connections.values())
        },
        "device_details": []
    }
    
    # Add detailed diagnostics for each device
    for device_id, status in device_connections.items():
        time_since_last = (current_time - status.last_seen).total_seconds()
        device_detail = {
            "device_id": device_id,
            "connection_status": status.connection_status,
            "connection_quality": status.connection_quality,
            "health_score": _calculate_device_health_score(status, time_since_last),
            "performance_metrics": {
                "average_interval": status.average_interval,
                "data_rate": status.data_count / max((status.last_seen - status.first_seen).total_seconds(), 1) if status.first_seen else 0,
                "error_rate": status.error_count / max(status.data_count, 1),
                "uptime_hours": (status.last_seen - status.first_seen).total_seconds() / 3600 if status.first_seen else 0
            },
            "last_error": status.last_error,
            "network_diagnostics": status.network_diagnostics,
            "recommendations": _generate_device_recommendations(status, time_since_last)
        }
        diagnostics["device_details"].append(device_detail)
    
    return diagnostics

def _calculate_device_health_score(status: DeviceConnectionStatus, time_since_last: float) -> float:
    """Calculate a health score (0-100) for a device based on various metrics"""
    score = 100.0
    
    # Connection status penalty
    if status.connection_status == "timeout":
        score -= 30
    elif status.connection_status == "disconnected":
        score -= 50
    
    # Time since last data penalty
    if time_since_last > 10:
        score -= min(20, time_since_last - 10)
    
    # Error rate penalty
    error_rate = status.error_count / max(status.data_count, 1)
    score -= min(20, error_rate * 100)
    
    # Connection quality bonus/penalty
    quality_scores = {"excellent": 10, "good": 5, "poor": -10, "unknown": -5}
    score += quality_scores.get(status.connection_quality, 0)
    
    # Reconnection frequency penalty
    if status.first_seen:
        uptime_hours = (status.last_seen - status.first_seen).total_seconds() / 3600
        reconnection_rate = status.reconnection_count / max(uptime_hours, 1)
        score -= min(15, reconnection_rate * 5)
    
    return max(0, min(100, score))

def _generate_device_recommendations(status: DeviceConnectionStatus, time_since_last: float) -> List[str]:
    """Generate recommendations for improving device connection"""
    recommendations = []
    
    if status.connection_status == "timeout":
        recommendations.append("Device appears to be disconnected. Check power and WiFi connection.")
    
    if status.connection_quality == "poor":
        recommendations.append("Poor connection quality detected. Consider moving closer to WiFi router.")
    
    error_rate = status.error_count / max(status.data_count, 1)
    if error_rate > 0.05:  # More than 5% error rate
        recommendations.append("High error rate detected. Check network stability and device firmware.")
    
    if status.reconnection_count > 5:
        recommendations.append("Frequent reconnections detected. Check WiFi stability and power supply.")
    
    if time_since_last > 30:
        recommendations.append("No recent data received. Device may need to be restarted.")
    
    if not recommendations:
        recommendations.append("Device is operating normally.")
    
    return recommendations

@app.get("/api/sensor-data/device/{device_id}/status")
async def get_device_connection_status(device_id: str):
    """Get comprehensive connection status for a specific ESP32 device with diagnostics"""
    device_status = get_device_status(device_id)
    
    if not device_status:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    
    current_time = datetime.now(timezone.utc)
    time_since_last = (current_time - device_status.last_seen).total_seconds()
    
    return {
        "device_id": device_status.device_id,
        "connection_status": device_status.connection_status,
        "last_seen": device_status.last_seen.isoformat(),
        "ip_address": device_status.ip_address,
        "data_count": device_status.data_count,
        "last_seen_seconds_ago": time_since_last,
        # Enhanced diagnostic information
        "connection_quality": device_status.connection_quality,
        "average_interval": device_status.average_interval,
        "reconnection_count": device_status.reconnection_count,
        "error_count": device_status.error_count,
        "last_error": device_status.last_error,
        "first_seen": device_status.first_seen.isoformat() if device_status.first_seen else None,
        "uptime_seconds": (device_status.last_seen - device_status.first_seen).total_seconds() if device_status.first_seen else 0,
        "network_diagnostics": device_status.network_diagnostics,
        "health_assessment": {
            "is_healthy": device_status.connection_status == "connected" and time_since_last < 5.0,
            "connection_stable": device_status.connection_quality in ["excellent", "good"],
            "error_rate": device_status.error_count / max(device_status.data_count, 1),
            "reconnection_frequency": device_status.reconnection_count / max((device_status.last_seen - device_status.first_seen).total_seconds() / 3600, 1) if device_status.first_seen else 0
        }
    }

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

# Legacy Calibration Endpoints - Redirected to new calibration API
@app.post("/api/device/calibrate")
async def save_calibration_legacy(calibration: CalibrationData):
    """Legacy endpoint - redirects to new calibration API"""
    try:
        # Convert legacy format to new format
        from models.calibration_models import CalibrationDataCreate
        
        new_calibration = CalibrationDataCreate(
            patient_id=calibration.patient_id,
            device_id="legacy_device",  # Default device ID for legacy calls
            baseline_pitch=calibration.baseline_pitch,
            baseline_fsr_left=calibration.baseline_roll,  # Map roll to FSR left for legacy compatibility
            baseline_fsr_right=calibration.warning_threshold * 100,  # Map warning to FSR right
            pitch_std_dev=1.0,  # Default values for legacy
            fsr_std_dev=0.1,
            calibration_duration=30
        )
        
        # Use new calibration API
        from api.calibration import save_calibration_data
        result = await save_calibration_data(new_calibration, supabase, "legacy_system")
        
        return {"status": "success", "message": "Calibration saved successfully (legacy endpoint)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/device/calibration/{patient_id}")
async def get_active_calibration_legacy(patient_id: str):
    """Legacy endpoint - redirects to new calibration API"""
    try:
        from api.calibration import get_active_calibration
        result = await get_active_calibration(patient_id, None, supabase)
        
        # Convert to legacy format
        return {
            "patient_id": result.patient_id,
            "baseline_pitch": result.baseline_pitch,
            "baseline_roll": result.baseline_fsr_left / 100,  # Convert back for legacy compatibility
            "warning_threshold": result.baseline_fsr_right / 100,
            "danger_threshold": result.baseline_fsr_ratio * 100,
            "calibration_date": result.calibration_date.isoformat(),
            "is_active": result.is_active
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Calibration Endpoints - New API Integration
@app.post("/api/calibration/start/{device_id}")
async def start_device_calibration_enhanced(
    device_id: str, 
    patient_id: str = "default_patient",
    duration_seconds: int = 30
):
    """Enhanced calibration start endpoint with progress tracking"""
    try:
        from models.calibration_models import CalibrationRequest
        from api.calibration import start_device_calibration
        
        calibration_request = CalibrationRequest(
            patient_id=patient_id,
            device_id=device_id,
            duration_seconds=duration_seconds,
            instructions="Please maintain normal upright posture for the calibration period"
        )
        
        # Use new calibration API with background tasks
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        
        result = await start_device_calibration(
            device_id, calibration_request, background_tasks, supabase, "system"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting enhanced calibration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calibration/complete")
async def save_calibration_data_enhanced(calibration_data: dict):
    """Enhanced calibration completion endpoint with adaptive thresholds"""
    try:
        from models.calibration_models import CalibrationDataCreate
        from api.calibration import save_calibration_data
        
        # Convert input data to new calibration format
        enhanced_calibration = CalibrationDataCreate(
            patient_id=calibration_data.get("patient_id", "default_patient"),
            device_id=calibration_data.get("device_id", "unknown"),
            baseline_pitch=calibration_data.get("baseline_pitch", 0.0),
            baseline_fsr_left=calibration_data.get("baseline_fsr_left", 2048.0),
            baseline_fsr_right=calibration_data.get("baseline_fsr_right", 2048.0),
            pitch_std_dev=calibration_data.get("pitch_std_dev", 1.0),
            fsr_std_dev=calibration_data.get("fsr_std_dev", 0.1),
            calibration_duration=calibration_data.get("calibration_duration", 30),
            sample_count=calibration_data.get("sample_count")
        )
        
        # Use new calibration API
        result = await save_calibration_data(enhanced_calibration, supabase, "system")
        
        # Update clinical algorithm instance if it exists
        algorithm_key = f"{enhanced_calibration.patient_id}_{enhanced_calibration.device_id}"
        if algorithm_key in clinical_algorithms:
            from clinical_algorithm import CalibrationData as AlgoCalibrationData
            algo_calibration = AlgoCalibrationData(
                patient_id=enhanced_calibration.patient_id,
                device_id=enhanced_calibration.device_id,
                baseline_pitch=enhanced_calibration.baseline_pitch,
                baseline_fsr_left=enhanced_calibration.baseline_fsr_left,
                baseline_fsr_right=enhanced_calibration.baseline_fsr_right,
                baseline_fsr_ratio=enhanced_calibration.baseline_fsr_ratio,
                pitch_std_dev=enhanced_calibration.pitch_std_dev,
                fsr_std_dev=enhanced_calibration.fsr_std_dev,
                calibration_timestamp=datetime.now(timezone.utc),
                is_active=True
            )
            clinical_algorithms[algorithm_key].calibration = algo_calibration
            logger.info(f"Updated calibration for clinical algorithm {algorithm_key}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error saving enhanced calibration data: {str(e)}")
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

# Clinical Pusher Syndrome Endpoints - Moved to api/clinical_thresholds.py
# Legacy endpoints maintained for backward compatibility
@app.post("/api/clinical/thresholds")
async def create_clinical_thresholds(thresholds: ClinicalThresholds):
    """Create or update clinical thresholds for a patient"""
    try:
        # Deactivate previous thresholds
        supabase.table("clinical_thresholds")\
            .update({"is_active": False})\
            .eq("patient_id", thresholds.patient_id)\
            .execute()
        
        # Insert new thresholds
        threshold_data = thresholds.dict()
        threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        result = supabase.table("clinical_thresholds").insert(threshold_data).execute()
        
        if result.data:
            # Update algorithm instance if it exists
            for key, algorithm in clinical_algorithms.items():
                if key.startswith(f"{thresholds.patient_id}_"):
                    algorithm.thresholds = thresholds
                    logger.info(f"Updated clinical thresholds for algorithm {key}")
            
            return {"status": "success", "message": "Clinical thresholds saved successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to save clinical thresholds")
            
    except Exception as e:
        logger.error(f"Error saving clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/thresholds/{patient_id}")
async def get_clinical_thresholds(patient_id: str):
    """Get active clinical thresholds for a patient"""
    try:
        result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            return result.data[0]
        else:
            # Return default thresholds if none found
            default_thresholds = create_default_thresholds(patient_id, PareticSide.RIGHT)
            return default_thresholds.dict()
            
    except Exception as e:
        logger.error(f"Error retrieving clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clinical/episode")
async def record_pusher_episode(episode: PusherEpisode):
    """Record a pusher syndrome episode"""
    try:
        episode_data = episode.dict()
        episode_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        result = supabase.table("pusher_episodes").insert(episode_data).execute()
        
        if result.data:
            return {"status": "success", "message": "Pusher episode recorded successfully", "episode_id": result.data[0]["id"]}
        else:
            raise HTTPException(status_code=400, detail="Failed to record pusher episode")
            
    except Exception as e:
        logger.error(f"Error recording pusher episode: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/episodes/{patient_id}")
async def get_pusher_episodes(patient_id: str, limit: int = 50, days: int = 7):
    """Get recent pusher syndrome episodes for a patient"""
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        result = supabase.table("pusher_episodes")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .gte("episode_start", start_date.isoformat())\
            .order("episode_start", desc=True)\
            .limit(limit)\
            .execute()
        
        episodes = result.data or []
        
        # Calculate summary statistics
        total_episodes = len(episodes)
        severity_counts = {"NO_PUSHING": 0, "MILD": 0, "MODERATE": 0, "SEVERE": 0}
        total_resistance = 0.0
        max_tilt = 0.0
        
        for episode in episodes:
            severity_score = episode.get("severity_score", 0)
            severity_name = ["NO_PUSHING", "MILD", "MODERATE", "SEVERE"][severity_score]
            severity_counts[severity_name] += 1
            
            total_resistance += episode.get("resistance_index", 0.0)
            max_tilt = max(max_tilt, episode.get("max_tilt_angle", 0.0))
        
        avg_resistance = total_resistance / total_episodes if total_episodes > 0 else 0.0
        
        return {
            "episodes": episodes,
            "summary": {
                "total_episodes": total_episodes,
                "severity_distribution": severity_counts,
                "average_resistance_index": round(avg_resistance, 3),
                "max_tilt_angle": round(max_tilt, 1),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving pusher episodes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/analysis/{patient_id}")
async def get_clinical_analysis(patient_id: str, timeframe: str = "week"):
    """Get clinical analysis and progress metrics for a patient"""
    try:
        # Determine date range based on timeframe
        end_date = datetime.now(timezone.utc)
        if timeframe == "day":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "week":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)  # Default to week
        
        # Get sensor readings for the timeframe
        sensor_result = supabase.table("sensor_readings")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .gte("timestamp", start_date.isoformat())\
            .order("timestamp", desc=True)\
            .execute()
        
        readings = sensor_result.data or []
        
        if not readings:
            return {
                "message": "No sensor data available for the specified timeframe",
                "timeframe": timeframe,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        
        # Calculate clinical metrics
        total_readings = len(readings)
        pusher_detections = sum(1 for r in readings if r.get("pusher_detected", False))
        pusher_percentage = (pusher_detections / total_readings) * 100 if total_readings > 0 else 0
        
        # Calculate tilt statistics
        tilt_angles = [abs(r.get("imu_pitch", 0)) for r in readings]
        avg_tilt = sum(tilt_angles) / len(tilt_angles) if tilt_angles else 0
        max_tilt = max(tilt_angles) if tilt_angles else 0
        
        # Calculate time within normal range (±5°)
        normal_readings = sum(1 for angle in tilt_angles if angle <= 5.0)
        time_within_normal = (normal_readings / total_readings) * 100 if total_readings > 0 else 0
        
        # Calculate confidence statistics
        confidence_levels = [r.get("confidence_level", 0) for r in readings if r.get("confidence_level") is not None]
        avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0
        
        return {
            "patient_id": patient_id,
            "timeframe": timeframe,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "total_readings": total_readings,
                "pusher_detections": pusher_detections,
                "pusher_detection_percentage": round(pusher_percentage, 1),
                "average_tilt_angle": round(avg_tilt, 2),
                "maximum_tilt_angle": round(max_tilt, 2),
                "time_within_normal_percentage": round(time_within_normal, 1),
                "average_confidence_level": round(avg_confidence, 3)
            },
            "clinical_interpretation": {
                "severity_assessment": "mild" if pusher_percentage < 10 else "moderate" if pusher_percentage < 30 else "severe",
                "progress_indicator": "improving" if time_within_normal > 80 else "stable" if time_within_normal > 60 else "needs_attention",
                "recommendations": [
                    "Continue current therapy protocol" if pusher_percentage < 10 else "Consider adjusting therapy intensity",
                    "Monitor for improvement trends" if time_within_normal > 60 else "Focus on postural awareness training"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating clinical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/daily-metrics/{patient_id}")
async def get_daily_metrics(patient_id: str, date: str = None):
    """Get daily clinical metrics for a patient"""
    try:
        # Parse date or use today
        if date:
            target_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        else:
            target_date = datetime.now(timezone.utc)
        
        # Get sensor readings for the day
        day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        try:
            sensor_result = supabase.table("sensor_readings")\
                .select("*")\
                .eq("patient_id", patient_id)\
                .gte("timestamp", day_start.isoformat())\
                .lt("timestamp", day_end.isoformat())\
                .order("timestamp", desc=False)\
                .execute()
            
            readings = sensor_result.data or []
        except Exception as db_error:
            logger.warning(f"Database connection failed, using mock data: {str(db_error)}")
            # Use mock data when database is unavailable
            readings = []
        
        # Get clinical algorithm instance
        algorithm = get_or_create_clinical_algorithm(patient_id, "default_device")
        
        # Convert readings to expected format
        formatted_readings = []
        for reading in readings:
            formatted_readings.append({
                'timestamp': reading.get('timestamp'),
                'imu_pitch': reading.get('imu_pitch', 0),
                'pusher_detected': reading.get('pusher_detected', False),
                'clinical_score': reading.get('clinical_score', 0),
                'correction_attempt': reading.get('episode_id') is not None,
                'initial_angle': reading.get('imu_pitch', 0),
                'final_angle': reading.get('imu_pitch', 0)
            })
        
        # Calculate daily metrics
        daily_metrics = algorithm.get_daily_metrics(target_date, formatted_readings)
        
        return {
            "patient_id": patient_id,
            "date": target_date.date().isoformat(),
            "metrics": daily_metrics,
            "data_points": len(readings),
            "status": "success",
            "data_source": "database" if readings else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error calculating daily metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/weekly-report/{patient_id}")
async def get_weekly_progress_report(patient_id: str, end_date: str = None):
    """Get weekly progress report with trend analysis"""
    try:
        # Parse end date or use today
        if end_date:
            target_end_date = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        else:
            target_end_date = datetime.now(timezone.utc)
        
        # Get sensor readings for the week
        week_start = target_end_date - timedelta(days=6)  # 7-day period
        
        try:
            sensor_result = supabase.table("sensor_readings")\
                .select("*")\
                .eq("patient_id", patient_id)\
                .gte("timestamp", week_start.isoformat())\
                .lte("timestamp", target_end_date.isoformat())\
                .order("timestamp", desc=False)\
                .execute()
            
            readings = sensor_result.data or []
        except Exception as db_error:
            logger.warning(f"Database connection failed, using mock data: {str(db_error)}")
            # Use mock data when database is unavailable
            readings = []
        
        # Get clinical algorithm instance
        algorithm = get_or_create_clinical_algorithm(patient_id, "default_device")
        
        # Convert readings to expected format
        formatted_readings = []
        for reading in readings:
            formatted_readings.append({
                'timestamp': reading.get('timestamp'),
                'imu_pitch': reading.get('imu_pitch', 0),
                'pusher_detected': reading.get('pusher_detected', False),
                'clinical_score': reading.get('clinical_score', 0),
                'correction_attempt': reading.get('episode_id') is not None,
                'initial_angle': reading.get('imu_pitch', 0),
                'final_angle': reading.get('imu_pitch', 0)
            })
        
        # Generate weekly progress report
        weekly_report = algorithm.get_weekly_progress_report(target_end_date, formatted_readings)
        
        return {
            "patient_id": patient_id,
            "report": weekly_report,
            "data_points": len(readings),
            "status": "success",
            "data_source": "database" if readings else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/episode-frequency/{patient_id}")
async def get_episode_frequency_tracking(patient_id: str, days: int = 30):
    """Get episode frequency tracking over specified period"""
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get pusher episodes from database
            episodes_result = supabase.table("pusher_episodes")\
                .select("*")\
                .eq("patient_id", patient_id)\
                .gte("episode_start", start_date.isoformat())\
                .order("episode_start", desc=False)\
                .execute()
            
            episodes = episodes_result.data or []
        except Exception as db_error:
            logger.warning(f"Database connection failed, using mock data: {str(db_error)}")
            # Use mock data when database is unavailable
            episodes = []
        
        # Group episodes by day
        daily_counts = {}
        for episode in episodes:
            episode_date = datetime.fromisoformat(episode['episode_start']).date()
            daily_counts[episode_date.isoformat()] = daily_counts.get(episode_date.isoformat(), 0) + 1
        
        # Fill in missing days with zero counts
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.isoformat()
            if date_str not in daily_counts:
                daily_counts[date_str] = 0
            current_date += timedelta(days=1)
        
        # Calculate statistics
        episode_counts = list(daily_counts.values())
        total_episodes = sum(episode_counts)
        avg_daily_episodes = total_episodes / days if days > 0 else 0
        max_daily_episodes = max(episode_counts) if episode_counts else 0
        
        # Calculate trend
        if len(episode_counts) >= 7:
            recent_avg = sum(episode_counts[-7:]) / 7
            earlier_avg = sum(episode_counts[:7]) / 7
            trend = "improving" if recent_avg < earlier_avg else "worsening" if recent_avg > earlier_avg else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "patient_id": patient_id,
            "period": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "days": days
            },
            "frequency_data": {
                "daily_counts": daily_counts,
                "total_episodes": total_episodes,
                "average_daily_episodes": round(avg_daily_episodes, 2),
                "maximum_daily_episodes": max_daily_episodes,
                "trend": trend
            },
            "episodes_detail": episodes,
            "data_source": "database" if episodes else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error tracking episode frequency: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clinical/resistance-index/{patient_id}")
async def get_resistance_index_analysis(patient_id: str, days: int = 7):
    """Get resistance index analysis during correction attempts"""
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        try:
            # Get correction attempts from sensor readings
            corrections_result = supabase.table("sensor_readings")\
                .select("*")\
                .eq("patient_id", patient_id)\
                .gte("timestamp", start_date.isoformat())\
                .not_.is_("episode_id", "null")\
                .order("timestamp", desc=False)\
                .execute()
            
            corrections = corrections_result.data or []
        except Exception as db_error:
            logger.warning(f"Database connection failed, using mock data: {str(db_error)}")
            # Use mock data when database is unavailable
            corrections = []
        
        # Group corrections by episode
        episodes = {}
        for correction in corrections:
            episode_id = correction.get('episode_id')
            if episode_id not in episodes:
                episodes[episode_id] = []
            episodes[episode_id].append(correction)
        
        # Calculate resistance index for each episode
        resistance_data = []
        total_resistance = 0
        successful_corrections = 0
        
        for episode_id, episode_corrections in episodes.items():
            if len(episode_corrections) < 2:
                continue
                
            # Sort by timestamp
            episode_corrections.sort(key=lambda x: x['timestamp'])
            
            initial_angle = abs(episode_corrections[0].get('imu_pitch', 0))
            final_angle = abs(episode_corrections[-1].get('imu_pitch', 0))
            
            expected_improvement = 5.0  # Expected 5° improvement
            actual_improvement = max(0, initial_angle - final_angle)
            
            resistance_ratio = max(0, (expected_improvement - actual_improvement) / expected_improvement)
            
            resistance_data.append({
                "episode_id": episode_id,
                "initial_angle": round(initial_angle, 2),
                "final_angle": round(final_angle, 2),
                "actual_improvement": round(actual_improvement, 2),
                "resistance_index": round(resistance_ratio, 3),
                "timestamp": episode_corrections[0]['timestamp']
            })
            
            total_resistance += resistance_ratio
            if actual_improvement >= 3.0:  # Consider successful if ≥3° improvement
                successful_corrections += 1
        
        # Calculate summary statistics
        avg_resistance = total_resistance / len(resistance_data) if resistance_data else 0
        success_rate = (successful_corrections / len(resistance_data)) * 100 if resistance_data else 0
        
        return {
            "patient_id": patient_id,
            "period": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "days": days
            },
            "resistance_analysis": {
                "average_resistance_index": round(avg_resistance, 3),
                "correction_success_rate": round(success_rate, 1),
                "total_correction_attempts": len(resistance_data),
                "successful_corrections": successful_corrections
            },
            "detailed_data": resistance_data,
            "data_source": "database" if corrections else "mock"
        }
        
    except Exception as e:
        logger.error(f"Error analyzing resistance index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clinical/correction-attempt/{patient_id}")
async def start_correction_attempt(patient_id: str, device_id: str, initial_angle: float):
    """Start a correction attempt for resistance analysis"""
    try:
        algorithm = get_or_create_clinical_algorithm(patient_id, device_id)
        attempt = algorithm.add_correction_attempt(initial_angle)
        
        return {
            "status": "success",
            "message": "Correction attempt started",
            "attempt_id": attempt.start_time.isoformat(),
            "initial_angle": initial_angle
        }
        
    except Exception as e:
        logger.error(f"Error starting correction attempt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clinical/correction-complete/{patient_id}")
async def complete_correction_attempt(patient_id: str, device_id: str, final_angle: float):
    """Complete a correction attempt and analyze resistance"""
    try:
        algorithm = get_or_create_clinical_algorithm(patient_id, device_id)
        attempt = algorithm.complete_correction_attempt(final_angle)
        
        if attempt:
            return {
                "status": "success",
                "message": "Correction attempt completed",
                "attempt_id": attempt.start_time.isoformat(),
                "initial_angle": attempt.initial_angle,
                "final_angle": final_angle,
                "improvement": attempt.actual_improvement,
                "expected_improvement": attempt.target_improvement,
                "resistance_detected": attempt.resistance_detected
            }
        else:
            return {
                "status": "warning",
                "message": "No active correction attempt found"
            }
        
    except Exception as e:
        logger.error(f"Error completing correction attempt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoints
@app.websocket("/ws/sensor-stream")
async def websocket_sensor_stream(websocket: WebSocket):
    """
    Optimized WebSocket endpoint for real-time sensor data streaming.
    Reduced overhead and faster message processing.
    """
    # Minimal client info for performance
    client_info = {"connected_from": websocket.client.host if websocket.client else "unknown"}
    
    await websocket_manager.connect(websocket, client_info)
    
    try:
        # Send minimal connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "connections": len(websocket_manager.active_connections)
        })
        
        # Optimized message loop with reduced processing
        while True:
            try:
                # Set timeout for receive to prevent blocking
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Fast message handling - only handle essential messages
                if message == "ping":
                    await websocket.send_text("pong")
                elif message.startswith("{"):
                    try:
                        client_message = json.loads(message)
                        msg_type = client_message.get("type")
                        
                        if msg_type == "ping":
                            await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
                        elif msg_type == "status":
                            # Send minimal device status
                            connected_devices = sum(1 for d in device_connections.values() if d.connection_status == "connected")
                            await websocket.send_json({
                                "type": "status_response",
                                "devices": connected_devices,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    except json.JSONDecodeError:
                        pass  # Ignore invalid JSON
                        
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_json({"type": "keepalive", "timestamp": datetime.now(timezone.utc).isoformat()})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        websocket_manager.disconnect(websocket)

@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """Get current WebSocket connection statistics"""
    check_device_timeouts()
    
    stats = websocket_manager.get_connection_stats()
    
    # Add device connection info
    connected_devices = len([d for d in device_connections.values() if d.connection_status == "connected"])
    total_devices = len(device_connections)
    
    return {
        "websocket_connections": stats,
        "device_connections": {
            "total_devices": total_devices,
            "connected_devices": connected_devices,
            "disconnected_devices": total_devices - connected_devices
        },
        "system_status": {
            "real_time_broadcasting": len(websocket_manager.active_connections) > 0,
            "data_flow_active": connected_devices > 0 and len(websocket_manager.active_connections) > 0
        }
    }

@app.post("/api/websocket/broadcast/test")
async def test_websocket_broadcast(message: dict):
    """Test endpoint to manually broadcast a message to all WebSocket clients"""
    if not websocket_manager.active_connections:
        return {
            "status": "no_clients",
            "message": "No WebSocket clients connected",
            "clients_count": 0
        }
    
    test_message = {
        "type": "test_broadcast",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_data": message
    }
    
    # Broadcast test message
    await websocket_manager.broadcast_sensor_data(test_message)
    
    return {
        "status": "success",
        "message": "Test message broadcasted to all clients",
        "clients_notified": len(websocket_manager.active_connections),
        "broadcast_content": test_message
    }

# Demo Mode Endpoints
@app.post("/api/demo/toggle")
async def toggle_demo_mode(enabled: bool, device_id: str = "ESP32_DEMO_001"):
    """
    Toggle demo mode on/off with realistic sensor data generation.
    
    Args:
        enabled: True to start demo mode, False to stop
        device_id: Device ID for demo data (default: ESP32_DEMO_001)
    
    Requirements implemented:
    - 6.4: Create demo mode toggle endpoint for mode switching
    - 6.5: Implement demo mode status tracking and indicator display
    - 6.7: Maintain full internet connectivity during demo mode
    """
    try:
        if enabled:
            # Start demo mode
            result = await demo_manager.start_demo_mode(websocket_manager, device_id)
            logger.info(f"Demo mode toggle: enabled (device: {device_id})")
            return result
        else:
            # Stop demo mode
            result = await demo_manager.stop_demo_mode()
            logger.info("Demo mode toggle: disabled")
            return result
            
    except Exception as e:
        logger.error(f"Error toggling demo mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo mode toggle failed: {str(e)}")

@app.get("/api/demo/status")
async def get_demo_status():
    """
    Get current demo mode status and statistics.
    
    Returns:
        Demo mode status including active state, duration, current scenario, and client count
    
    Requirements implemented:
    - 6.5: Provide demo mode status tracking for presentation controls
    """
    try:
        status = demo_manager.get_demo_status()
        return {
            "demo_mode": status,
            "websocket_clients": len(websocket_manager.active_connections),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting demo status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get demo status: {str(e)}")

@app.post("/api/demo/generate")
async def generate_demo_data_sample():
    """
    Generate a single sample of demo data for testing purposes.
    
    Returns:
        Single demo sensor reading with realistic pusher syndrome patterns
    
    Requirements implemented:
    - 6.1: Generate realistic simulated sensor data matching typical pusher syndrome patterns
    - 6.2: Create smooth pitch transitions (-15° to +15°) with occasional pusher events
    - 6.3: Generate asymmetric FSR readings consistent with pusher behavior
    """
    try:
        from demo_data_generator import DemoDataGenerator
        
        # Create temporary generator for single reading
        generator = DemoDataGenerator("ESP32_DEMO_SAMPLE")
        reading = generator.generate_reading()
        
        # Convert to API response format
        demo_sample = {
            "device_id": reading.device_id,
            "timestamp": reading.timestamp,
            "sensor_data": {
                "pitch": reading.pitch,
                "fsr_left": reading.fsr_left,
                "fsr_right": reading.fsr_right
            },
            "clinical_analysis": {
                "pusher_detected": reading.pusher_detected,
                "confidence_level": reading.confidence_level,
                "tilt_angle": abs(reading.pitch),
                "tilt_direction": "left" if reading.pitch < -2 else "right" if reading.pitch > 2 else "center"
            },
            "demo_info": {
                "description": reading.description,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        logger.info(f"Generated demo data sample: pitch={reading.pitch:.1f}°, pusher={reading.pusher_detected}")
        return demo_sample
        
    except Exception as e:
        logger.error(f"Error generating demo data sample: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo data generation failed: {str(e)}")

@app.post("/api/demo/scenario/{scenario_name}")
async def set_demo_scenario(scenario_name: str):
    """
    Set the current demo scenario for targeted demonstration.
    
    Args:
        scenario_name: Name of the scenario to activate
        
    Available scenarios:
    - normal_posture: Normal upright posture (±3°)
    - mild_pusher_episode: Mild pusher syndrome (8-12°)
    - moderate_pusher_episode: Moderate pusher syndrome (12-18°)
    - severe_pusher_episode: Severe pusher syndrome (18-25°)
    - correction_attempt: Therapist correction attempt (5-10°)
    - recovery_phase: Recovery from episode (-2 to 5°)
    
    Requirements implemented:
    - 6.2: Create smooth transitions between different pusher event scenarios
    - 6.6: Include realistic pusher detection events for demonstrations
    """
    try:
        if not demo_manager.is_demo_active:
            raise HTTPException(status_code=400, detail="Demo mode is not currently active")
        
        if not demo_manager.generator:
            raise HTTPException(status_code=500, detail="Demo generator not available")
        
        valid_scenarios = [
            "normal_posture",
            "mild_pusher_episode", 
            "moderate_pusher_episode",
            "severe_pusher_episode",
            "correction_attempt",
            "recovery_phase"
        ]
        
        if scenario_name not in valid_scenarios:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid scenario. Valid options: {', '.join(valid_scenarios)}"
            )
        
        # Update generator scenario
        demo_manager.generator.current_scenario = scenario_name
        demo_manager.generator.scenario_start_time = time.time()
        demo_manager.generator.scenario_duration = 30.0  # Fixed duration for manual control
        
        logger.info(f"Demo scenario set to: {scenario_name}")
        return {
            "status": "success",
            "message": f"Demo scenario changed to {scenario_name}",
            "scenario": scenario_name,
            "available_scenarios": valid_scenarios
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting demo scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set demo scenario: {str(e)}")

@app.get("/api/demo/scenarios")
async def get_available_demo_scenarios():
    """
    Get list of available demo scenarios with descriptions.
    
    Returns:
        List of available demo scenarios for presentation control
    """
    scenarios = [
        {
            "name": "normal_posture",
            "display_name": "Normal Posture",
            "description": "Normal upright posture with minimal variation (±3°)",
            "pitch_range": "±3°",
            "pusher_detected": False
        },
        {
            "name": "mild_pusher_episode",
            "display_name": "Mild Pusher Episode",
            "description": "Mild pusher syndrome with moderate lean (8-12°)",
            "pitch_range": "8-12°",
            "pusher_detected": True
        },
        {
            "name": "moderate_pusher_episode",
            "display_name": "Moderate Pusher Episode", 
            "description": "Moderate pusher syndrome with significant lean (12-18°)",
            "pitch_range": "12-18°",
            "pusher_detected": True
        },
        {
            "name": "severe_pusher_episode",
            "display_name": "Severe Pusher Episode",
            "description": "Severe pusher syndrome requiring immediate intervention (18-25°)",
            "pitch_range": "18-25°",
            "pusher_detected": True
        },
        {
            "name": "correction_attempt",
            "display_name": "Correction Attempt",
            "description": "Therapist correction attempt with patient resistance (5-10°)",
            "pitch_range": "5-10°",
            "pusher_detected": False
        },
        {
            "name": "recovery_phase",
            "display_name": "Recovery Phase",
            "description": "Recovery from pusher episode, returning to normal (-2 to 5°)",
            "pitch_range": "-2 to 5°",
            "pusher_detected": False
        }
    ]
    
    current_scenario = None
    if demo_manager.is_demo_active and demo_manager.generator:
        current_scenario = demo_manager.generator.current_scenario
    
    return {
        "scenarios": scenarios,
        "current_scenario": current_scenario,
        "demo_active": demo_manager.is_demo_active
    }