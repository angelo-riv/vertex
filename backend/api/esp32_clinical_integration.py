# ESP32 Clinical Integration API Endpoints
# Requirements: 19.5, 19.6 - Integration with existing alert and authentication systems

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging
from security.auth_middleware import (
    require_therapist_role, 
    require_clinical_access, 
    require_patient_access,
    get_current_user
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clinical", tags=["ESP32 Clinical Integration"])

# Pydantic models for clinical threshold management
class ClinicalThresholds(BaseModel):
    patient_id: str
    paretic_side: str = Field(..., regex="^(left|right)$")
    normal_threshold: float = Field(default=5.0, ge=1.0, le=15.0)
    pusher_threshold: float = Field(default=10.0, ge=5.0, le=25.0)
    severe_threshold: float = Field(default=20.0, ge=10.0, le=45.0)
    resistance_threshold: float = Field(default=2.0, ge=0.5, le=5.0)
    episode_duration_min: float = Field(default=2.0, ge=0.5, le=10.0)
    created_by: Optional[str] = None

class ThresholdResponse(BaseModel):
    id: str
    patient_id: str
    paretic_side: str
    normal_threshold: float
    pusher_threshold: float
    severe_threshold: float
    resistance_threshold: float
    episode_duration_min: float
    created_by: str
    is_active: bool
    created_at: datetime

class ESP32AlertPreferences(BaseModel):
    patient_id: str
    connection_alerts: bool = True
    pusher_alerts: bool = True
    calibration_reminders: bool = True
    threshold_alerts: bool = True
    alert_volume: str = Field(default="medium", regex="^(low|medium|high|muted)$")

class ClinicalNotification(BaseModel):
    notification_type: str = Field(..., regex="^(esp32_connection|esp32_disconnection|pusher_detected|calibration_reminder|threshold_breach)$")
    patient_id: str
    message: str
    severity: str = Field(default="info", regex="^(info|warning|error|success)$")
    metadata: Optional[Dict[str, Any]] = None

# Clinical threshold management endpoints
@router.post("/thresholds", response_model=ThresholdResponse)
async def create_clinical_thresholds(
    thresholds: ClinicalThresholds,
    request: Request,
    user: dict = Depends(require_therapist_role())
):
    """
    Create or update patient-specific clinical thresholds.
    Requires therapist role permissions.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # Validate threshold relationships
        if thresholds.normal_threshold >= thresholds.pusher_threshold:
            raise HTTPException(
                status_code=400,
                detail="Normal threshold must be less than pusher threshold"
            )
        
        if thresholds.pusher_threshold >= thresholds.severe_threshold:
            raise HTTPException(
                status_code=400,
                detail="Pusher threshold must be less than severe threshold"
            )
        
        # Set created_by from authenticated user
        thresholds.created_by = user.get("user_email") or user.get("user_id")
        
        # In a real implementation, save to database
        # For now, return mock response
        threshold_response = ThresholdResponse(
            id=f"threshold_{thresholds.patient_id}_{int(datetime.now().timestamp())}",
            patient_id=thresholds.patient_id,
            paretic_side=thresholds.paretic_side,
            normal_threshold=thresholds.normal_threshold,
            pusher_threshold=thresholds.pusher_threshold,
            severe_threshold=thresholds.severe_threshold,
            resistance_threshold=thresholds.resistance_threshold,
            episode_duration_min=thresholds.episode_duration_min,
            created_by=thresholds.created_by,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"Clinical thresholds created for patient {thresholds.patient_id} by {thresholds.created_by}")
        
        return threshold_response
        
    except Exception as e:
        logger.error(f"Failed to create clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create clinical thresholds")

@router.get("/thresholds/{patient_id}", response_model=ThresholdResponse)
async def get_clinical_thresholds(
    patient_id: str,
    request: Request,
    user: dict = Depends(require_patient_access(patient_id))
):
    """
    Get active clinical thresholds for a patient.
    Patients can access their own data, therapists can access any patient data.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # In a real implementation, fetch from database
        # For now, return mock response with default values
        threshold_response = ThresholdResponse(
            id=f"threshold_{patient_id}_default",
            patient_id=patient_id,
            paretic_side="right",
            normal_threshold=5.0,
            pusher_threshold=10.0,
            severe_threshold=20.0,
            resistance_threshold=2.0,
            episode_duration_min=2.0,
            created_by="system",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        return threshold_response
        
    except Exception as e:
        logger.error(f"Failed to get clinical thresholds for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Clinical thresholds not found")

@router.get("/thresholds", response_model=List[ThresholdResponse])
async def list_clinical_thresholds(
    request: Request,
    user: dict = Depends(require_clinical_access())
):
    """
    List all clinical thresholds (for clinical staff only).
    Requires clinical access permissions.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # In a real implementation, fetch from database with proper filtering
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Failed to list clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list clinical thresholds")

# ESP32 alert preference management
@router.post("/alert-preferences")
async def set_esp32_alert_preferences(
    preferences: ESP32AlertPreferences,
    request: Request,
    user: dict = Depends(require_patient_access(preferences.patient_id))
):
    """
    Set ESP32 alert preferences for a patient.
    Patients can set their own preferences, therapists can set for any patient.
    
    Requirements: 19.5 - Integration with existing alert systems
    """
    try:
        # In a real implementation, save to database
        logger.info(f"ESP32 alert preferences updated for patient {preferences.patient_id}")
        
        return {
            "success": True,
            "message": "Alert preferences updated successfully",
            "preferences": preferences.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to set ESP32 alert preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update alert preferences")

@router.get("/alert-preferences/{patient_id}")
async def get_esp32_alert_preferences(
    patient_id: str,
    request: Request,
    user: dict = Depends(require_patient_access(patient_id))
):
    """
    Get ESP32 alert preferences for a patient.
    
    Requirements: 19.5 - Integration with existing alert systems
    """
    try:
        # In a real implementation, fetch from database
        # For now, return default preferences
        default_preferences = ESP32AlertPreferences(
            patient_id=patient_id,
            connection_alerts=True,
            pusher_alerts=True,
            calibration_reminders=True,
            threshold_alerts=True,
            alert_volume="medium"
        )
        
        return default_preferences
        
    except Exception as e:
        logger.error(f"Failed to get ESP32 alert preferences for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert preferences")

# Clinical notification endpoints
@router.post("/notifications")
async def send_clinical_notification(
    notification: ClinicalNotification,
    request: Request,
    user: dict = Depends(require_clinical_access())
):
    """
    Send clinical notification for ESP32 events.
    Requires clinical access permissions.
    
    Requirements: 19.5 - Integration with existing alert systems
    """
    try:
        # In a real implementation, integrate with notification system
        # For now, log the notification
        logger.info(f"Clinical notification sent: {notification.notification_type} for patient {notification.patient_id}")
        
        return {
            "success": True,
            "message": "Notification sent successfully",
            "notification_id": f"notif_{int(datetime.now().timestamp())}"
        }
        
    except Exception as e:
        logger.error(f"Failed to send clinical notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.get("/notifications/{patient_id}")
async def get_clinical_notifications(
    patient_id: str,
    limit: int = 50,
    request: Request,
    user: dict = Depends(require_patient_access(patient_id))
):
    """
    Get clinical notifications for a patient.
    
    Requirements: 19.5 - Integration with existing alert systems
    """
    try:
        # In a real implementation, fetch from database
        # For now, return empty list
        return {
            "notifications": [],
            "total": 0,
            "patient_id": patient_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get clinical notifications for patient {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")

# ESP32 device management for therapists
@router.post("/devices/{device_id}/assign")
async def assign_esp32_device(
    device_id: str,
    patient_id: str,
    request: Request,
    user: dict = Depends(require_therapist_role())
):
    """
    Assign ESP32 device to a patient.
    Requires therapist role permissions.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # In a real implementation, update device assignment in database
        logger.info(f"ESP32 device {device_id} assigned to patient {patient_id} by {user.get('user_email')}")
        
        return {
            "success": True,
            "message": f"Device {device_id} assigned to patient {patient_id}",
            "device_id": device_id,
            "patient_id": patient_id,
            "assigned_by": user.get("user_email") or user.get("user_id"),
            "assigned_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to assign ESP32 device: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assign device")

@router.delete("/devices/{device_id}/assign")
async def unassign_esp32_device(
    device_id: str,
    request: Request,
    user: dict = Depends(require_therapist_role())
):
    """
    Unassign ESP32 device from patient.
    Requires therapist role permissions.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # In a real implementation, remove device assignment in database
        logger.info(f"ESP32 device {device_id} unassigned by {user.get('user_email')}")
        
        return {
            "success": True,
            "message": f"Device {device_id} unassigned successfully",
            "device_id": device_id,
            "unassigned_by": user.get("user_email") or user.get("user_id"),
            "unassigned_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to unassign ESP32 device: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unassign device")

@router.get("/devices")
async def list_esp32_devices(
    request: Request,
    user: dict = Depends(require_clinical_access())
):
    """
    List all ESP32 devices and their assignments.
    Requires clinical access permissions.
    
    Requirements: 19.6 - Integration with existing authentication systems
    """
    try:
        # In a real implementation, fetch from database
        # For now, return mock device list
        mock_devices = [
            {
                "device_id": "ESP32_001",
                "device_name": "Vertex Device #1",
                "patient_id": None,
                "connection_status": "disconnected",
                "last_seen": None,
                "firmware_version": "1.0.0"
            },
            {
                "device_id": "ESP32_002", 
                "device_name": "Vertex Device #2",
                "patient_id": "patient_123",
                "connection_status": "connected",
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "firmware_version": "1.0.0"
            }
        ]
        
        return {
            "devices": mock_devices,
            "total": len(mock_devices)
        }
        
    except Exception as e:
        logger.error(f"Failed to list ESP32 devices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list devices")

# Health check endpoint for ESP32 integration
@router.get("/health")
async def esp32_integration_health():
    """
    Health check for ESP32 clinical integration endpoints.
    Public endpoint for system monitoring.
    """
    return {
        "status": "healthy",
        "service": "ESP32 Clinical Integration",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "clinical_thresholds": True,
            "alert_preferences": True,
            "device_management": True,
            "notifications": True,
            "role_based_access": True
        }
    }