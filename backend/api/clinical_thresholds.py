"""
Clinical Thresholds Management API Endpoints
Provides CRUD operations for patient-specific clinical thresholds with version history and therapist authorization.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
from supabase import Client

from models.clinical_models import (
    ClinicalThresholdsCreate, ClinicalThresholdsUpdate, ClinicalThresholdsResponse,
    ThresholdHistoryEntry, ThresholdValidationResult, PatientThresholdSummary,
    ThresholdComparisonResult, BulkThresholdOperation, ThresholdAnalytics,
    ThresholdPreset, ThresholdAuditLog, PareticSide,
    validate_threshold_consistency, create_threshold_preset
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clinical/thresholds", tags=["Clinical Thresholds"])


def get_supabase_client() -> Client:
    """Dependency to get Supabase client - will be injected by main app"""
    # This will be overridden by the main app's dependency injection
    pass


def get_current_user(request: Request) -> Optional[str]:
    """Extract current user/therapist ID from request headers or auth"""
    # In production, this would extract from JWT token or session
    return request.headers.get("X-Therapist-ID", "system")


def log_threshold_audit(
    supabase: Client,
    patient_id: str,
    threshold_id: str,
    action: str,
    performed_by: str,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    reason: Optional[str] = None,
    request: Optional[Request] = None
):
    """Log threshold changes for audit trail"""
    try:
        audit_data = {
            "patient_id": patient_id,
            "threshold_id": threshold_id,
            "action": action,
            "performed_by": performed_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_values": old_values,
            "new_values": new_values,
            "reason": reason
        }
        
        if request:
            audit_data["ip_address"] = request.client.host if request.client else None
            audit_data["user_agent"] = request.headers.get("User-Agent")
        
        # In production, store in audit log table
        logger.info(f"Threshold audit: {action} for patient {patient_id} by {performed_by}")
        
    except Exception as e:
        logger.error(f"Failed to log threshold audit: {str(e)}")


@router.post("/", response_model=ClinicalThresholdsResponse)
async def create_clinical_thresholds(
    thresholds: ClinicalThresholdsCreate,
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user),
    request: Request = None
):
    """
    Create new clinical thresholds for a patient.
    Validates threshold consistency and deactivates previous versions.
    """
    try:
        # Validate threshold consistency
        validation = validate_threshold_consistency(thresholds)
        if not validation.is_valid:
            raise HTTPException(
                status_code=422, 
                detail={
                    "message": "Threshold validation failed",
                    "errors": validation.errors,
                    "warnings": validation.warnings
                }
            )
        
        # Set created_by if not provided
        if not thresholds.created_by:
            thresholds.created_by = current_user
        
        # Deactivate previous thresholds for this patient
        supabase.table("clinical_thresholds")\
            .update({"is_active": False})\
            .eq("patient_id", thresholds.patient_id)\
            .execute()
        
        # Insert new thresholds
        threshold_data = thresholds.dict()
        threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
        threshold_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = supabase.table("clinical_thresholds").insert(threshold_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create clinical thresholds")
        
        created_threshold = result.data[0]
        
        # Log audit trail
        log_threshold_audit(
            supabase, thresholds.patient_id, created_threshold["id"],
            "create", current_user, None, threshold_data,
            "Created new clinical thresholds", request
        )
        
        logger.info(f"Created clinical thresholds for patient {thresholds.patient_id} by {current_user}")
        
        return ClinicalThresholdsResponse(**created_threshold)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{patient_id}", response_model=ClinicalThresholdsResponse)
async def get_clinical_thresholds(
    patient_id: str,
    version: Optional[int] = Query(None, description="Specific version to retrieve"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get active clinical thresholds for a patient.
    Optionally retrieve a specific version.
    """
    try:
        query = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)
        
        if version:
            query = query.eq("version", version)
        else:
            query = query.eq("is_active", True)
        
        result = query.order("created_at", desc=True).limit(1).execute()
        
        if not result.data:
            # Return default thresholds if none found
            from clinical_algorithm import create_default_thresholds, PareticSide as AlgoPareticSide
            default_thresholds = create_default_thresholds(patient_id, AlgoPareticSide.RIGHT)
            
            # Convert to response format
            return ClinicalThresholdsResponse(
                id="default",
                patient_id=patient_id,
                paretic_side=PareticSide.RIGHT,
                normal_threshold=default_thresholds.normal_threshold,
                pusher_threshold=default_thresholds.pusher_threshold,
                severe_threshold=default_thresholds.severe_threshold,
                resistance_threshold=default_thresholds.resistance_threshold,
                episode_duration_min=default_thresholds.episode_duration_min,
                non_paretic_threshold=default_thresholds.non_paretic_threshold,
                created_by="system",
                therapist_notes="Default system thresholds",
                is_active=True,
                version=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
        
        return ClinicalThresholdsResponse(**result.data[0])
        
    except Exception as e:
        logger.error(f"Error retrieving clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{patient_id}", response_model=ClinicalThresholdsResponse)
async def update_clinical_thresholds(
    patient_id: str,
    updates: ClinicalThresholdsUpdate,
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user),
    request: Request = None
):
    """
    Update clinical thresholds for a patient.
    Creates a new version and archives the previous one.
    """
    try:
        # Get current active thresholds
        current_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .execute()
        
        if not current_result.data:
            raise HTTPException(status_code=404, detail="No active thresholds found for patient")
        
        current_thresholds = current_result.data[0]
        
        # Prepare updated data
        update_data = updates.dict(exclude_unset=True)
        
        # Merge with current values
        merged_data = {**current_thresholds, **update_data}
        merged_data["created_by"] = current_user
        merged_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Validate merged thresholds
        validation_data = ClinicalThresholdsCreate(**{
            k: v for k, v in merged_data.items() 
            if k in ClinicalThresholdsCreate.__fields__
        })
        validation = validate_threshold_consistency(validation_data)
        
        if not validation.is_valid:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Updated threshold validation failed",
                    "errors": validation.errors,
                    "warnings": validation.warnings
                }
            )
        
        # Deactivate current thresholds
        supabase.table("clinical_thresholds")\
            .update({"is_active": False})\
            .eq("id", current_thresholds["id"])\
            .execute()
        
        # Create new version
        new_threshold_data = {
            k: v for k, v in merged_data.items()
            if k not in ["id", "version", "created_at"]
        }
        new_threshold_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        result = supabase.table("clinical_thresholds").insert(new_threshold_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to update clinical thresholds")
        
        updated_threshold = result.data[0]
        
        # Log audit trail
        log_threshold_audit(
            supabase, patient_id, updated_threshold["id"],
            "update", current_user, current_thresholds, new_threshold_data,
            updates.change_reason or "Updated clinical thresholds", request
        )
        
        logger.info(f"Updated clinical thresholds for patient {patient_id} by {current_user}")
        
        return ClinicalThresholdsResponse(**updated_threshold)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{patient_id}")
async def delete_clinical_thresholds(
    patient_id: str,
    reason: str = Query(..., description="Reason for deletion"),
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user),
    request: Request = None
):
    """
    Deactivate clinical thresholds for a patient.
    Does not permanently delete, but marks as inactive.
    """
    try:
        # Get current active thresholds
        current_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .execute()
        
        if not current_result.data:
            raise HTTPException(status_code=404, detail="No active thresholds found for patient")
        
        current_thresholds = current_result.data[0]
        
        # Deactivate thresholds
        result = supabase.table("clinical_thresholds")\
            .update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", current_thresholds["id"])\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to deactivate clinical thresholds")
        
        # Log audit trail
        log_threshold_audit(
            supabase, patient_id, current_thresholds["id"],
            "delete", current_user, current_thresholds, None,
            reason, request
        )
        
        logger.info(f"Deactivated clinical thresholds for patient {patient_id} by {current_user}")
        
        return {"status": "success", "message": "Clinical thresholds deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting clinical thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{patient_id}/history", response_model=List[ThresholdHistoryEntry])
async def get_threshold_history(
    patient_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of history entries to retrieve"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get version history of clinical thresholds for a patient.
    """
    try:
        result = supabase.table("clinical_threshold_history")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .order("version", desc=True)\
            .limit(limit)\
            .execute()
        
        return [ThresholdHistoryEntry(**entry) for entry in result.data or []]
        
    except Exception as e:
        logger.error(f"Error retrieving threshold history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{patient_id}/summary", response_model=PatientThresholdSummary)
async def get_patient_threshold_summary(
    patient_id: str,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of patient's threshold configuration and calibration status.
    """
    try:
        # Get current thresholds
        threshold_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .execute()
        
        # Get threshold count
        count_result = supabase.table("clinical_thresholds")\
            .select("version", count="exact")\
            .eq("patient_id", patient_id)\
            .execute()
        
        # Get calibration status
        calibration_result = supabase.table("device_calibrations")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("is_active", True)\
            .order("calibration_date", desc=True)\
            .limit(1)\
            .execute()
        
        if not threshold_result.data:
            # Return default summary
            return PatientThresholdSummary(
                patient_id=patient_id,
                current_version=0,
                paretic_side=PareticSide.RIGHT,
                threshold_ranges={
                    "normal": 5.0,
                    "pusher_relevant": 10.0,
                    "severe": 20.0
                },
                last_updated=datetime.now(timezone.utc),
                updated_by="system",
                total_versions=0,
                is_calibrated=False,
                calibration_date=None
            )
        
        current_threshold = threshold_result.data[0]
        calibration = calibration_result.data[0] if calibration_result.data else None
        
        return PatientThresholdSummary(
            patient_id=patient_id,
            current_version=current_threshold["version"],
            paretic_side=PareticSide(current_threshold["paretic_side"]),
            threshold_ranges={
                "normal": current_threshold["normal_threshold"],
                "pusher_relevant": current_threshold["pusher_threshold"],
                "severe": current_threshold["severe_threshold"]
            },
            last_updated=datetime.fromisoformat(current_threshold["updated_at"]),
            updated_by=current_threshold["created_by"],
            total_versions=count_result.count or 0,
            is_calibrated=calibration is not None,
            calibration_date=datetime.fromisoformat(calibration["calibration_date"]) if calibration else None
        )
        
    except Exception as e:
        logger.error(f"Error retrieving patient threshold summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{patient_id}/validate", response_model=ThresholdValidationResult)
async def validate_thresholds(
    patient_id: str,
    thresholds: ClinicalThresholdsCreate
):
    """
    Validate clinical thresholds without saving them.
    Useful for real-time validation in UI.
    """
    try:
        # Override patient_id to match URL parameter
        thresholds.patient_id = patient_id
        
        validation = validate_threshold_consistency(thresholds)
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{patient_id}/compare/{version_a}/{version_b}", response_model=ThresholdComparisonResult)
async def compare_threshold_versions(
    patient_id: str,
    version_a: int,
    version_b: int,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Compare two versions of clinical thresholds for a patient.
    """
    try:
        # Get both versions
        version_a_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("version", version_a)\
            .execute()
        
        version_b_result = supabase.table("clinical_thresholds")\
            .select("*")\
            .eq("patient_id", patient_id)\
            .eq("version", version_b)\
            .execute()
        
        if not version_a_result.data or not version_b_result.data:
            raise HTTPException(status_code=404, detail="One or both threshold versions not found")
        
        threshold_a = version_a_result.data[0]
        threshold_b = version_b_result.data[0]
        
        # Compare fields
        comparison_fields = [
            "paretic_side", "normal_threshold", "pusher_threshold", "severe_threshold",
            "resistance_threshold", "episode_duration_min", "non_paretic_threshold"
        ]
        
        changes = {}
        for field in comparison_fields:
            value_a = threshold_a.get(field)
            value_b = threshold_b.get(field)
            
            if value_a != value_b:
                change_type = "modified"
                if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
                    if value_b > value_a:
                        change_type = "increased"
                    else:
                        change_type = "decreased"
                
                changes[field] = {
                    "old_value": value_a,
                    "new_value": value_b,
                    "change_type": change_type
                }
        
        # Generate summary
        if not changes:
            change_summary = "No changes between versions"
            clinical_impact = "No clinical impact"
        else:
            change_count = len(changes)
            change_summary = f"{change_count} field(s) changed: {', '.join(changes.keys())}"
            
            # Assess clinical impact
            critical_changes = [k for k in changes.keys() if k in ["pusher_threshold", "severe_threshold"]]
            if critical_changes:
                clinical_impact = "High - Critical thresholds modified"
            elif len(changes) > 3:
                clinical_impact = "Medium - Multiple parameters changed"
            else:
                clinical_impact = "Low - Minor adjustments"
        
        return ThresholdComparisonResult(
            patient_id=patient_id,
            version_a=version_a,
            version_b=version_b,
            changes=changes,
            change_summary=change_summary,
            clinical_impact=clinical_impact
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing threshold versions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/presets/", response_model=List[ThresholdPreset])
async def get_threshold_presets():
    """
    Get predefined threshold presets for common conditions.
    """
    try:
        presets = [
            create_threshold_preset("Acute Stroke - Mild", "acute_stroke", "mild"),
            create_threshold_preset("Acute Stroke - Moderate", "acute_stroke", "moderate"),
            create_threshold_preset("Acute Stroke - Severe", "acute_stroke", "severe"),
            create_threshold_preset("Chronic Stroke - Mild", "chronic_stroke", "mild"),
            create_threshold_preset("Chronic Stroke - Moderate", "chronic_stroke", "moderate"),
            create_threshold_preset("Chronic Stroke - Severe", "chronic_stroke", "severe"),
        ]
        
        return presets
        
    except Exception as e:
        logger.error(f"Error retrieving threshold presets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{patient_id}/apply-preset")
async def apply_threshold_preset(
    patient_id: str,
    preset_name: str,
    paretic_side: PareticSide,
    supabase: Client = Depends(get_supabase_client),
    current_user: str = Depends(get_current_user),
    request: Request = None
):
    """
    Apply a predefined threshold preset to a patient.
    """
    try:
        # Get available presets
        presets = await get_threshold_presets()
        selected_preset = next((p for p in presets if p.name == preset_name), None)
        
        if not selected_preset:
            raise HTTPException(status_code=404, detail="Threshold preset not found")
        
        # Create thresholds from preset
        threshold_data = selected_preset.thresholds.dict()
        threshold_data["patient_id"] = patient_id
        threshold_data["paretic_side"] = paretic_side.value
        threshold_data["created_by"] = current_user
        threshold_data["therapist_notes"] = f"Applied preset: {preset_name}"
        
        thresholds = ClinicalThresholdsCreate(**threshold_data)
        
        # Create thresholds using existing endpoint logic
        return await create_clinical_thresholds(thresholds, supabase, current_user, request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying threshold preset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")