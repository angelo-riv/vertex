"""
Clinical data models for threshold management and patient-specific configuration.
Supports CRUD operations, version history, and therapist authorization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class PareticSide(str, Enum):
    """Paretic side configuration for directional analysis"""
    LEFT = "left"
    RIGHT = "right"


class ThresholdRange(BaseModel):
    """Configurable threshold range with validation"""
    normal: float = Field(..., ge=0.0, le=15.0, description="Normal lean threshold in degrees")
    pusher_relevant: float = Field(..., ge=5.0, le=25.0, description="Pusher-relevant threshold in degrees") 
    severe: float = Field(..., ge=15.0, le=45.0, description="Severe lean threshold in degrees")
    
    @validator('pusher_relevant')
    def pusher_must_be_greater_than_normal(cls, v, values):
        if 'normal' in values and v <= values['normal']:
            raise ValueError('Pusher threshold must be greater than normal threshold')
        return v
    
    @validator('severe')
    def severe_must_be_greater_than_pusher(cls, v, values):
        if 'pusher_relevant' in values and v <= values['pusher_relevant']:
            raise ValueError('Severe threshold must be greater than pusher threshold')
        return v


class ClinicalThresholdsCreate(BaseModel):
    """Model for creating new clinical thresholds"""
    patient_id: str = Field(..., min_length=1, description="Patient UUID")
    paretic_side: PareticSide = Field(..., description="Paretic side for directional analysis")
    normal_threshold: float = Field(default=5.0, ge=0.0, le=15.0, description="Normal lean threshold in degrees")
    pusher_threshold: float = Field(default=10.0, ge=5.0, le=25.0, description="Pusher-relevant threshold in degrees")
    severe_threshold: float = Field(default=20.0, ge=15.0, le=45.0, description="Severe lean threshold in degrees")
    resistance_threshold: float = Field(default=2.0, ge=0.5, le=5.0, description="Resistance detection threshold")
    episode_duration_min: float = Field(default=2.0, ge=1.0, le=10.0, description="Minimum episode duration in seconds")
    non_paretic_threshold: float = Field(default=0.7, ge=0.5, le=0.9, description="Non-paretic limb use threshold (0-1)")
    created_by: Optional[str] = Field(None, description="Therapist ID or username")
    therapist_notes: Optional[str] = Field(None, max_length=1000, description="Clinical notes from therapist")
    
    @validator('pusher_threshold')
    def validate_pusher_threshold(cls, v, values):
        if 'normal_threshold' in values and v <= values['normal_threshold']:
            raise ValueError('Pusher threshold must be greater than normal threshold')
        return v
    
    @validator('severe_threshold')
    def validate_severe_threshold(cls, v, values):
        if 'pusher_threshold' in values and v <= values['pusher_threshold']:
            raise ValueError('Severe threshold must be greater than pusher threshold')
        return v


class ClinicalThresholdsUpdate(BaseModel):
    """Model for updating existing clinical thresholds"""
    paretic_side: Optional[PareticSide] = None
    normal_threshold: Optional[float] = Field(None, ge=0.0, le=15.0)
    pusher_threshold: Optional[float] = Field(None, ge=5.0, le=25.0)
    severe_threshold: Optional[float] = Field(None, ge=15.0, le=45.0)
    resistance_threshold: Optional[float] = Field(None, ge=0.5, le=5.0)
    episode_duration_min: Optional[float] = Field(None, ge=1.0, le=10.0)
    non_paretic_threshold: Optional[float] = Field(None, ge=0.5, le=0.9)
    created_by: Optional[str] = None
    therapist_notes: Optional[str] = Field(None, max_length=1000)
    change_reason: Optional[str] = Field(None, max_length=500, description="Reason for threshold change")


class ClinicalThresholdsResponse(BaseModel):
    """Model for clinical thresholds API responses"""
    id: str
    patient_id: str
    paretic_side: PareticSide
    normal_threshold: float
    pusher_threshold: float
    severe_threshold: float
    resistance_threshold: float
    episode_duration_min: float
    non_paretic_threshold: float
    created_by: Optional[str]
    therapist_notes: Optional[str]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ThresholdHistoryEntry(BaseModel):
    """Model for threshold version history"""
    id: str
    threshold_id: str
    patient_id: str
    version: int
    paretic_side: PareticSide
    normal_threshold: float
    pusher_threshold: float
    severe_threshold: float
    resistance_threshold: float
    episode_duration_min: float
    non_paretic_threshold: float
    created_by: Optional[str]
    therapist_notes: Optional[str]
    change_reason: Optional[str]
    created_at: datetime
    archived_at: datetime
    
    class Config:
        from_attributes = True


class ThresholdValidationResult(BaseModel):
    """Model for threshold validation results"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []


class PatientThresholdSummary(BaseModel):
    """Summary model for patient threshold overview"""
    patient_id: str
    current_version: int
    paretic_side: PareticSide
    threshold_ranges: ThresholdRange
    last_updated: datetime
    updated_by: Optional[str]
    total_versions: int
    is_calibrated: bool
    calibration_date: Optional[datetime]


class ThresholdComparisonResult(BaseModel):
    """Model for comparing threshold versions"""
    patient_id: str
    version_a: int
    version_b: int
    changes: Dict[str, Dict[str, Any]]  # field_name -> {old_value, new_value, change_type}
    change_summary: str
    clinical_impact: str


class BulkThresholdOperation(BaseModel):
    """Model for bulk threshold operations"""
    operation: str = Field(..., pattern="^(create|update|delete|activate|deactivate)$")
    patient_ids: List[str] = Field(..., min_items=1, max_items=100)
    threshold_data: Optional[ClinicalThresholdsCreate] = None
    update_data: Optional[ClinicalThresholdsUpdate] = None
    created_by: str = Field(..., description="Therapist performing bulk operation")
    reason: str = Field(..., max_length=500, description="Reason for bulk operation")


class ThresholdAnalytics(BaseModel):
    """Model for threshold usage analytics"""
    patient_id: str
    timeframe_days: int
    threshold_effectiveness: Dict[str, float]  # threshold_name -> effectiveness_score
    episode_reduction: float  # Percentage reduction in episodes
    average_severity_change: float
    compliance_score: float
    recommendations: List[str]


class ThresholdPreset(BaseModel):
    """Model for predefined threshold presets"""
    name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    condition_type: str = Field(..., description="Stroke type or condition")
    severity_level: str = Field(..., pattern="^(mild|moderate|severe)$")
    thresholds: ClinicalThresholdsCreate
    created_by: str
    usage_count: int = 0
    effectiveness_rating: Optional[float] = Field(None, ge=0.0, le=5.0)


class ThresholdAuditLog(BaseModel):
    """Model for threshold change audit logging"""
    id: str
    patient_id: str
    threshold_id: str
    action: str = Field(..., pattern="^(create|update|delete|activate|deactivate)$")
    performed_by: str
    timestamp: datetime
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True


# Validation functions
def validate_threshold_consistency(thresholds: ClinicalThresholdsCreate) -> ThresholdValidationResult:
    """Validate threshold consistency and clinical appropriateness"""
    errors = []
    warnings = []
    recommendations = []
    
    # Check threshold ordering
    if thresholds.pusher_threshold <= thresholds.normal_threshold:
        errors.append("Pusher threshold must be greater than normal threshold")
    
    if thresholds.severe_threshold <= thresholds.pusher_threshold:
        errors.append("Severe threshold must be greater than pusher threshold")
    
    # Check clinical appropriateness
    if thresholds.normal_threshold > 7.0:
        warnings.append("Normal threshold above 7° may be too permissive for clinical use")
    
    if thresholds.pusher_threshold < 8.0:
        warnings.append("Pusher threshold below 8° may cause false positives")
    
    if thresholds.severe_threshold > 25.0:
        warnings.append("Severe threshold above 25° may miss critical episodes")
    
    if thresholds.episode_duration_min < 1.5:
        warnings.append("Episode duration below 1.5s may cause noise in detection")
    
    if thresholds.non_paretic_threshold > 0.8:
        recommendations.append("Consider lowering non-paretic threshold for better sensitivity")
    
    # Clinical recommendations based on paretic side
    if thresholds.paretic_side == PareticSide.LEFT:
        recommendations.append("Left paretic side: Monitor for rightward leaning patterns")
    else:
        recommendations.append("Right paretic side: Monitor for leftward leaning patterns")
    
    return ThresholdValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        recommendations=recommendations
    )


def create_threshold_preset(name: str, condition: str, severity: str) -> ThresholdPreset:
    """Create predefined threshold presets for common conditions"""
    
    # Base thresholds for different severity levels
    severity_configs = {
        "mild": {
            "normal_threshold": 6.0,
            "pusher_threshold": 12.0,
            "severe_threshold": 22.0,
            "resistance_threshold": 1.5,
            "episode_duration_min": 2.5,
            "non_paretic_threshold": 0.65
        },
        "moderate": {
            "normal_threshold": 5.0,
            "pusher_threshold": 10.0,
            "severe_threshold": 20.0,
            "resistance_threshold": 2.0,
            "episode_duration_min": 2.0,
            "non_paretic_threshold": 0.7
        },
        "severe": {
            "normal_threshold": 4.0,
            "pusher_threshold": 8.0,
            "severe_threshold": 18.0,
            "resistance_threshold": 2.5,
            "episode_duration_min": 1.5,
            "non_paretic_threshold": 0.75
        }
    }
    
    config = severity_configs.get(severity, severity_configs["moderate"])
    
    thresholds = ClinicalThresholdsCreate(
        patient_id="preset",  # Will be replaced when applied
        paretic_side=PareticSide.RIGHT,  # Default, will be configured per patient
        **config
    )
    
    return ThresholdPreset(
        name=name,
        description=f"{severity.title()} pusher syndrome thresholds for {condition}",
        condition_type=condition,
        severity_level=severity,
        thresholds=thresholds,
        created_by="system"
    )