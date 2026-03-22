"""
Calibration Data Integration API Endpoints
Provides calibration data management, adaptive threshold calculation, and real-time analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from supabase import Client
import asyncio

from models.calibration_models import (
    CalibrationDataCreate, CalibrationDataResponse, AdaptiveThresholds,
    CalibrationRequest, CalibrationProgress, CalibrationSummary,
    CalibrationValidationResult, FSRImbalanceAnalysis, PitchDeviationAnalysis,
    CalibrationStatus, calculate_adaptive_thresholds, validate_calibration_quality,
    analyze_fsr_imbalance, analyze_pitch_deviation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calibration", tags=["Calibration"])

# In-memory calibration progress tracking (in production, use Redis or database)
calibration_sessions: Dict[str, CalibrationProgress] = {}


def get_supabase_client() -> Client:
    """Dependency to get Supabase client - will be injected by main app"""
    pass


def get_current_user(request: Request) -> Optional[str]:
    """Extract current user/therapist ID from request headers or auth"""
    return request.headers.get("X-Therapist-ID", "system")


@router.post("/start/{device_id}")
async def start_device_calibration(
    device_id: str,
    calibration_request: CalibrationRequest,
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user)
):
    """
    Start calibration process for an ESP32 device.
    This endpoint initiates the calibration and tracks progress.
    """
    try:
        # Validate device exists and is connected
        session_key = f"{calibration_request.patient_id}_{device_id}"
        
        # Check if calibration is already in progress
        if session_key in calibration_sessions:
            existing_session = calibration_sessions[session_key]
            if existing_session.status == CalibrationStatus.CALIBRATING:
                return {
                    "status": "already_in_progress",
                    "message": "Calibration already in progress for this device",
                    "progress": existing_session
                }
        
        # Create new calibration session
        calibration_progress = CalibrationProgress(
            patient_id=calibration_request.patient_id,
            device_id=device_id,
            status=CalibrationStatus.CALIBRATING,
            progress_percentage=0.0,
            remaining_seconds=calibration_request.duration_seconds,
            current_sample_count=0,
            instructions=calibration_request.instructions or "Please maintain normal upright posture for 30 seconds",
            started_at=datetime.now(timezone.utc)
        )
        
        calibration_sessions[session_key] = calibration_progress
        
        # Schedule calibration timeout cleanup
        background_tasks.add_task(
            cleanup_calibration_session, 
            session_key, 
            calibration_request.duration_seconds + 60  # Extra 60 seconds buffer
        )
        
        logger.info(f"Calibration started for device {device_id}, patient {calibration_request.patient_id} by {current_user}")
        
        return {
            "status": "success",
            "message": f"Calibration started for device {device_id}",
            "calibration_duration": calibration_request.duration_seconds,
            "session_key": session_key,
            "instructions": calibration_progress.instructions,
            "progress": calibration_progress
        }
        
    except Exception as e:
        logger.error(f"Error starting calibration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{patient_id}/{device_id}")
async def get_calibration_progress(
    patient_id: str,
    device_id: str
):
    """
    Get current calibration progress for a device.
    """
    try:
        session_key = f"{patient_id}_{device_id}"
        
        if session_key not in calibration_sessions:
            return {
                "status": "not_found",
                "message": "No active calibration session found",
                "progress": None
            }
        
        progress = calibration_sessions[session_key]
        
        # Update remaining time if still calibrating
        if progress.status == CalibrationStatus.CALIBRATING and progress.started_at:
            elapsed = (datetime.now(timezone.utc) - progress.started_at).total_seconds()
            progress.remaining_seconds = max(0, 30 - int(elapsed))  # Default 30 seconds
            progress.progress_percentage = min(100.0, (elapsed / 30) * 100)
            
            # Auto-complete if time expired
            if progress.remaining_seconds <= 0:
                progress.status = CalibrationStatus.CALIBRATED
                progress.progress_percentage = 100.0
        
        return {
            "status": "success",
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"Error getting calibration progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def save_calibration_data(
    calibration: CalibrationDataCreate,
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user)
):
    """
    Save completed calibration data from ESP32 and calculate adaptive thresholds.
    """
    try:
        # Validate calibration quality
        validation = validate_calibration_quality(calibration)
        
        if not validation.is_valid:
            logger.warning(f"Poor calibration quality for device {calibration.device_id}: {validation.warnings}")
            # Continue with warning but don't reject
        
        # Get current clinical thresholds for adaptive calculation
        thresholds_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", calibration.patient_id)\
            .eq("is_active", True)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        clinical_thresholds = {}
        if thresholds_result.data:
            threshold_data = thresholds_result.data[0]
            clinical_thresholds = {
                'normal_threshold': threshold_data.get('normal_threshold', 5.0),
                'pusher_threshold': threshold_data.get('pusher_threshold', 10.0),
                'severe_threshold': threshold_data.get('severe_threshold', 20.0)
            }
        else:
            # Use default thresholds
            clinical_thresholds = {
                'normal_threshold': 5.0,
                'pusher_threshold': 10.0,
                'severe_threshold': 20.0
            }
        
        # Calculate adaptive thresholds
        adaptive_thresholds = calculate_adaptive_thresholds(calibration, clinical_thresholds)
        
        # Deactivate previous calibrations for this patient/device
        supabase.table("device_calibrations")\
            .update({"is_active": False})\
            .eq("patient_id", calibration.patient_id)\
            .eq("device_id", calibration.device_id)\
            .execute()
        
        # Prepare calibration data for database
        calibration_data = calibration.dict()
        calibration_data["calibration_date"] = datetime.now(timezone.utc).isoformat()
        calibration_data["baseline_fsr_ratio"] = calibration.baseline_fsr_ratio
        calibration_data["is_active"] = True
        
        # Insert new calibration
        result = supabase.table("device_calibrations").insert(calibration_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to save calibration data")
        
        saved_calibration = result.data[0]
        adaptive_thresholds.calibration_id = saved_calibration["id"]
        
        # Update calibration session status
        session_key = f"{calibration.patient_id}_{calibration.device_id}"
        if session_key in calibration_sessions:
            calibration_sessions[session_key].status = CalibrationStatus.CALIBRATED
            calibration_sessions[session_key].progress_percentage = 100.0
            calibration_sessions[session_key].remaining_seconds = 0
        
        logger.info(f"Calibration data saved for device {calibration.device_id}, patient {calibration.patient_id}")
        
        return {
            "status": "success",
            "message": "Calibration data saved successfully",
            "calibration_id": saved_calibration["id"],
            "validation": validation,
            "baseline_values": {
                "pitch": calibration.baseline_pitch,
                "fsr_left": calibration.baseline_fsr_left,
                "fsr_right": calibration.baseline_fsr_right,
                "fsr_ratio": calibration.baseline_fsr_ratio,
                "pitch_std_dev": calibration.pitch_std_dev,
                "fsr_std_dev": calibration.fsr_std_dev
            },
            "adaptive_thresholds": adaptive_thresholds.dict(),
            "quality_score": validation.quality_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving calibration data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}", response_model=CalibrationDataResponse)
async def get_active_calibration(
    patient_id: str,
    device_id: Optional[str] = Query(None, description="Specific device ID to filter by"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get active calibration data for a patient, optionally filtered by device.
    """
    try:
        query = supabase.table("device_calibrations")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .order("calibration_date", desc=True)
        
        if device_id:
            query = query.eq("device_id", device_id)
        
        result = query.limit(1).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No active calibration found")
        
        calibration_data = result.data[0]
        
        # Calculate baseline_fsr_ratio if not present
        if not calibration_data.get("baseline_fsr_ratio"):
            fsr_left = calibration_data.get("baseline_fsr_left", 0)
            fsr_right = calibration_data.get("baseline_fsr_right", 0)
            total = fsr_left + fsr_right
            calibration_data["baseline_fsr_ratio"] = fsr_right / total if total > 0 else 0.5
        
        return CalibrationDataResponse(**calibration_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving calibration data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{patient_id}/summary", response_model=CalibrationSummary)
async def get_calibration_summary(
    patient_id: str,
    device_id: Optional[str] = Query(None),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get comprehensive calibration summary for a patient.
    """
    try:
        # Get active calibration
        query = supabase.table("device_calibrations")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .order("calibration_date", desc=True)
        
        if device_id:
            query = query.eq("device_id", device_id)
        
        active_result = query.limit(1).execute()
        
        # Get calibration count
        count_query = supabase.table("device_calibrations")\
            .select("id", count="exact")\
            .eq("patient_id", patient_id)
        
        if device_id:
            count_query = count_query.eq("device_id", device_id)
        
        count_result = count_query.execute()
        
        # Determine status and get data
        if active_result.data:
            calibration_data = active_result.data[0]
            last_calibration_date = datetime.fromisoformat(calibration_data["calibration_date"])
            days_since = (datetime.now(timezone.utc) - last_calibration_date).days
            
            # Check if recalibration is needed (>7 days old)
            needs_recalibration = days_since > 7
            status = CalibrationStatus.EXPIRED if needs_recalibration else CalibrationStatus.CALIBRATED
            
            baseline_values = {
                "pitch": calibration_data.get("baseline_pitch"),
                "fsr_left": calibration_data.get("baseline_fsr_left"),
                "fsr_right": calibration_data.get("baseline_fsr_right"),
                "fsr_ratio": calibration_data.get("baseline_fsr_ratio"),
                "pitch_std_dev": calibration_data.get("pitch_std_dev"),
                "fsr_std_dev": calibration_data.get("fsr_std_dev")
            }
            
            # Calculate adaptive thresholds if needed
            adaptive_thresholds = None
            try:
                # Get clinical thresholds
                thresholds_result = supabase.table("clinical_thresholds")\
                    .select("*")\
                    .eq("patient_id", patient_id)\
                    .eq("is_active", True)\
                    .limit(1)\
                    .execute()
                
                if thresholds_result.data:
                    clinical_thresholds = {
                        'normal_threshold': thresholds_result.data[0].get('normal_threshold', 5.0),
                        'pusher_threshold': thresholds_result.data[0].get('pusher_threshold', 10.0),
                        'severe_threshold': thresholds_result.data[0].get('severe_threshold', 20.0)
                    }
                    
                    # Create calibration object for threshold calculation
                    calibration_obj = CalibrationDataCreate(
                        patient_id=patient_id,
                        device_id=calibration_data.get("device_id", "unknown"),
                        baseline_pitch=calibration_data.get("baseline_pitch", 0.0),
                        baseline_fsr_left=calibration_data.get("baseline_fsr_left", 2048.0),
                        baseline_fsr_right=calibration_data.get("baseline_fsr_right", 2048.0),
                        pitch_std_dev=calibration_data.get("pitch_std_dev", 1.0),
                        fsr_std_dev=calibration_data.get("fsr_std_dev", 0.1)
                    )
                    
                    adaptive_thresholds = calculate_adaptive_thresholds(calibration_obj, clinical_thresholds)
                    adaptive_thresholds.calibration_id = calibration_data["id"]
            except Exception as e:
                logger.warning(f"Could not calculate adaptive thresholds: {str(e)}")
        else:
            status = CalibrationStatus.NOT_CALIBRATED
            last_calibration_date = None
            days_since = None
            needs_recalibration = True
            baseline_values = None
            adaptive_thresholds = None
        
        return CalibrationSummary(
            patient_id=patient_id,
            device_id=device_id,
            status=status,
            last_calibration_date=last_calibration_date,
            baseline_values=baseline_values,
            adaptive_thresholds=adaptive_thresholds,
            calibration_count=count_result.count or 0,
            days_since_last_calibration=days_since,
            needs_recalibration=needs_recalibration
        )
        
    except Exception as e:
        logger.error(f"Error getting calibration summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{patient_id}/analyze-fsr")
async def analyze_fsr_imbalance_endpoint(
    patient_id: str,
    fsr_left: int = Query(..., ge=0, le=4095),
    fsr_right: int = Query(..., ge=0, le=4095),
    device_id: Optional[str] = Query(None),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Analyze FSR imbalance using calibrated ratios and adaptive thresholds.
    """
    try:
        # Get active calibration
        calibration_response = await get_active_calibration(patient_id, device_id, supabase)
        
        # Get clinical thresholds for adaptive threshold calculation
        thresholds_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .limit(1)\
            .execute()
        
        clinical_thresholds = {}
        if thresholds_result.data:
            threshold_data = thresholds_result.data[0]
            clinical_thresholds = {
                'normal_threshold': threshold_data.get('normal_threshold', 5.0),
                'pusher_threshold': threshold_data.get('pusher_threshold', 10.0),
                'severe_threshold': threshold_data.get('severe_threshold', 20.0)
            }
        else:
            clinical_thresholds = {'normal_threshold': 5.0, 'pusher_threshold': 10.0, 'severe_threshold': 20.0}
        
        # Calculate adaptive thresholds
        calibration_obj = CalibrationDataCreate(
            patient_id=patient_id,
            device_id=calibration_response.device_id,
            baseline_pitch=calibration_response.baseline_pitch,
            baseline_fsr_left=calibration_response.baseline_fsr_left,
            baseline_fsr_right=calibration_response.baseline_fsr_right,
            pitch_std_dev=calibration_response.pitch_std_dev,
            fsr_std_dev=calibration_response.fsr_std_dev
        )
        
        adaptive_thresholds = calculate_adaptive_thresholds(calibration_obj, clinical_thresholds)
        
        # Analyze FSR imbalance
        analysis = analyze_fsr_imbalance(fsr_left, fsr_right, calibration_response, adaptive_thresholds)
        
        return {
            "status": "success",
            "analysis": analysis,
            "adaptive_thresholds": {
                "normal_fsr_imbalance": adaptive_thresholds.normal_fsr_imbalance_threshold,
                "pusher_fsr_imbalance": adaptive_thresholds.pusher_fsr_imbalance_threshold,
                "severe_fsr_imbalance": adaptive_thresholds.severe_fsr_imbalance_threshold
            },
            "calibration_baseline": {
                "fsr_ratio": calibration_response.baseline_fsr_ratio,
                "fsr_left": calibration_response.baseline_fsr_left,
                "fsr_right": calibration_response.baseline_fsr_right
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing FSR imbalance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{patient_id}/analyze-pitch")
async def analyze_pitch_deviation_endpoint(
    patient_id: str,
    current_pitch: float = Query(..., ge=-180.0, le=180.0),
    device_id: Optional[str] = Query(None),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Analyze pitch deviation from calibrated upright position using adaptive thresholds.
    """
    try:
        # Get active calibration
        calibration_response = await get_active_calibration(patient_id, device_id, supabase)
        
        # Get clinical thresholds for adaptive threshold calculation
        thresholds_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .limit(1)\
            .execute()
        
        clinical_thresholds = {}
        if thresholds_result.data:
            threshold_data = thresholds_result.data[0]
            clinical_thresholds = {
                'normal_threshold': threshold_data.get('normal_threshold', 5.0),
                'pusher_threshold': threshold_data.get('pusher_threshold', 10.0),
                'severe_threshold': threshold_data.get('severe_threshold', 20.0)
            }
        else:
            clinical_thresholds = {'normal_threshold': 5.0, 'pusher_threshold': 10.0, 'severe_threshold': 20.0}
        
        # Calculate adaptive thresholds
        calibration_obj = CalibrationDataCreate(
            patient_id=patient_id,
            device_id=calibration_response.device_id,
            baseline_pitch=calibration_response.baseline_pitch,
            baseline_fsr_left=calibration_response.baseline_fsr_left,
            baseline_fsr_right=calibration_response.baseline_fsr_right,
            pitch_std_dev=calibration_response.pitch_std_dev,
            fsr_std_dev=calibration_response.fsr_std_dev
        )
        
        adaptive_thresholds = calculate_adaptive_thresholds(calibration_obj, clinical_thresholds)
        
        # Analyze pitch deviation
        analysis = analyze_pitch_deviation(current_pitch, calibration_response, adaptive_thresholds)
        
        return {
            "status": "success",
            "analysis": analysis,
            "adaptive_thresholds": {
                "normal_pitch": adaptive_thresholds.normal_pitch_threshold,
                "pusher_pitch": adaptive_thresholds.pusher_pitch_threshold,
                "severe_pitch": adaptive_thresholds.severe_pitch_threshold
            },
            "calibration_baseline": {
                "pitch": calibration_response.baseline_pitch,
                "pitch_std_dev": calibration_response.pitch_std_dev
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing pitch deviation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{patient_id}")
async def deactivate_calibration(
    patient_id: str,
    device_id: Optional[str] = Query(None),
    reason: str = Query(..., description="Reason for deactivation"),
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user)
):
    """
    Deactivate calibration data for a patient/device.
    """
    try:
        query = supabase.table("device_calibrations")\
            .update({"is_active": False})\
            .eq("patient_id", patient_id)
        
        if device_id:
            query = query.eq("device_id", device_id)
        
        result = query.execute()
        
        # Clean up any active calibration sessions
        if device_id:
            session_key = f"{patient_id}_{device_id}"
            if session_key in calibration_sessions:
                del calibration_sessions[session_key]
        else:
            # Remove all sessions for this patient
            keys_to_remove = [key for key in calibration_sessions.keys() if key.startswith(f"{patient_id}_")]
            for key in keys_to_remove:
                del calibration_sessions[key]
        
        logger.info(f"Calibration deactivated for patient {patient_id}, device {device_id or 'all'} by {current_user}, reason: {reason}")
        
        return {
            "status": "success",
            "message": "Calibration data deactivated successfully",
            "affected_records": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        logger.error(f"Error deactivating calibration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def cleanup_calibration_session(session_key: str, delay_seconds: int):
    """
    Background task to clean up calibration sessions after timeout.
    """
    await asyncio.sleep(delay_seconds)
    if session_key in calibration_sessions:
        session = calibration_sessions[session_key]
        if session.status == CalibrationStatus.CALIBRATING:
            session.status = CalibrationStatus.EXPIRED
        # Keep session for a while for status queries, but mark as expired
        logger.info(f"Calibration session {session_key} marked as expired after timeout")