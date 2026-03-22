"""
Calibration data models for patient-specific baseline establishment and adaptive thresholds.
Supports ESP32 calibration integration and real-time threshold adaptation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class CalibrationStatus(str, Enum):
    """Calibration status tracking"""
    NOT_CALIBRATED = "not_calibrated"
    CALIBRATING = "calibrating"
    CALIBRATED = "calibrated"
    EXPIRED = "expired"


class CalibrationDataCreate(BaseModel):
    """Model for creating new calibration data from ESP32"""
    patient_id: str = Field(..., min_length=1, description="Patient UUID")
    device_id: str = Field(..., min_length=1, description="ESP32 device identifier")
    baseline_pitch: float = Field(..., description="Calibrated upright pitch angle in degrees")
    baseline_fsr_left: float = Field(..., ge=0, le=4095, description="Baseline left FSR reading")
    baseline_fsr_right: float = Field(..., ge=0, le=4095, description="Baseline right FSR reading")
    pitch_std_dev: float = Field(..., ge=0, description="Standard deviation of pitch during calibration")
    fsr_std_dev: float = Field(..., ge=0, description="Standard deviation of FSR ratio during calibration")
    calibration_duration: int = Field(default=30, ge=10, le=60, description="Calibration duration in seconds")
    sample_count: Optional[int] = Field(None, ge=1, description="Number of samples collected during calibration")
    
    @validator('baseline_fsr_left', 'baseline_fsr_right')
    def validate_fsr_readings(cls, v):
        if v < 100:  # Minimum pressure threshold
            raise ValueError('FSR readings should be above minimum pressure threshold (100)')
        return v
    
    @property
    def baseline_fsr_ratio(self) -> float:
        """Calculate baseline FSR ratio (right/(left+right))"""
        total = self.baseline_fsr_left + self.baseline_fsr_right
        if total == 0:
            return 0.5
        return self.baseline_fsr_right / total


class CalibrationDataResponse(BaseModel):
    """Model for calibration data API responses"""
    id: str
    patient_id: str
    device_id: str
    calibration_date: datetime
    baseline_pitch: float
    baseline_fsr_left: float
    baseline_fsr_right: float
    baseline_fsr_ratio: float
    pitch_std_dev: float
    fsr_std_dev: float
    calibration_duration: int
    sample_count: Optional[int]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdaptiveThresholds(BaseModel):
    """Model for adaptive thresholds calculated from calibration data"""
    patient_id: str
    device_id: str
    calibration_id: str
    
    # Pitch-based thresholds (relative to calibrated upright)
    normal_pitch_threshold: float = Field(description="Normal pitch deviation threshold")
    pusher_pitch_threshold: float = Field(description="Pusher-relevant pitch deviation threshold")
    severe_pitch_threshold: float = Field(description="Severe pitch deviation threshold")
    
    # FSR-based thresholds (relative to calibrated baseline)
    normal_fsr_imbalance_threshold: float = Field(description="Normal FSR imbalance threshold")
    pusher_fsr_imbalance_threshold: float = Field(description="Pusher-relevant FSR imbalance threshold")
    severe_fsr_imbalance_threshold: float = Field(description="Severe FSR imbalance threshold")
    
    # Resistance detection thresholds
    resistance_force_threshold: float = Field(description="Force threshold for resistance detection")
    resistance_angle_threshold: float = Field(description="Angle threshold for resistance detection")
    
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


class CalibrationRequest(BaseModel):
    """Model for calibration request from frontend"""
    patient_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    duration_seconds: int = Field(default=30, ge=10, le=60)
    instructions: Optional[str] = Field(None, max_length=500)


class CalibrationProgress(BaseModel):
    """Model for calibration progress tracking"""
    patient_id: str
    device_id: str
    status: CalibrationStatus
    progress_percentage: float = Field(ge=0, le=100)
    remaining_seconds: int = Field(ge=0)
    current_sample_count: int = Field(ge=0)
    instructions: str
    started_at: Optional[datetime] = None


class CalibrationSummary(BaseModel):
    """Summary model for patient calibration overview"""
    patient_id: str
    device_id: Optional[str]
    status: CalibrationStatus
    last_calibration_date: Optional[datetime]
    baseline_values: Optional[Dict[str, float]]
    adaptive_thresholds: Optional[AdaptiveThresholds]
    calibration_count: int
    days_since_last_calibration: Optional[int]
    needs_recalibration: bool


class CalibrationValidationResult(BaseModel):
    """Model for calibration data validation results"""
    is_valid: bool
    quality_score: float = Field(ge=0, le=1, description="Calibration quality score (0-1)")
    warnings: List[str] = []
    recommendations: List[str] = []
    baseline_stability: Dict[str, float] = Field(description="Stability metrics for baseline values")


class FSRImbalanceAnalysis(BaseModel):
    """Model for FSR imbalance analysis using calibrated ratios"""
    current_ratio: float
    baseline_ratio: float
    imbalance_magnitude: float = Field(description="Absolute deviation from baseline")
    imbalance_direction: str = Field(description="Direction of imbalance (left/right/balanced)")
    severity_level: str = Field(description="Severity classification (normal/moderate/severe)")
    exceeds_threshold: bool
    confidence_level: float = Field(ge=0, le=1)


class PitchDeviationAnalysis(BaseModel):
    """Model for pitch deviation analysis from calibrated upright position"""
    current_pitch: float
    baseline_pitch: float
    deviation_magnitude: float = Field(description="Absolute deviation from calibrated upright")
    deviation_direction: str = Field(description="Direction of deviation (left/right/forward/backward)")
    severity_level: str = Field(description="Severity classification (normal/moderate/severe)")
    exceeds_threshold: bool
    confidence_level: float = Field(ge=0, le=1)


# Utility functions for calibration data processing
def calculate_adaptive_thresholds(calibration: CalibrationDataCreate, 
                                clinical_thresholds: Dict[str, float]) -> AdaptiveThresholds:
    """
    Calculate adaptive thresholds based on calibration data and clinical parameters.
    Uses baseline ± 2 standard deviations approach.
    """
    # Pitch-based adaptive thresholds (relative to calibrated upright)
    pitch_multiplier = 2.0  # 2 standard deviations
    normal_pitch = clinical_thresholds.get('normal_threshold', 5.0)
    pusher_pitch = clinical_thresholds.get('pusher_threshold', 10.0)
    severe_pitch = clinical_thresholds.get('severe_threshold', 20.0)
    
    # Adjust thresholds based on calibration stability
    stability_factor = min(1.0, calibration.pitch_std_dev / 2.0)  # More stable = tighter thresholds
    
    # FSR-based adaptive thresholds (relative to calibrated baseline)
    fsr_multiplier = 2.0  # 2 standard deviations
    normal_fsr_imbalance = fsr_multiplier * calibration.fsr_std_dev
    pusher_fsr_imbalance = normal_fsr_imbalance * 1.5
    severe_fsr_imbalance = normal_fsr_imbalance * 2.5
    
    # Resistance detection thresholds (baseline + 2*SD)
    resistance_force = (calibration.baseline_fsr_left + calibration.baseline_fsr_right) / 2 + \
                      (fsr_multiplier * calibration.fsr_std_dev * 1000)  # Convert to force units
    resistance_angle = calibration.baseline_pitch + (pitch_multiplier * calibration.pitch_std_dev)
    
    return AdaptiveThresholds(
        patient_id=calibration.patient_id,
        device_id=calibration.device_id,
        calibration_id="pending",  # Will be set after database insertion
        
        # Pitch thresholds adjusted for individual baseline
        normal_pitch_threshold=normal_pitch * (1 + stability_factor),
        pusher_pitch_threshold=pusher_pitch * (1 + stability_factor),
        severe_pitch_threshold=severe_pitch * (1 + stability_factor),
        
        # FSR imbalance thresholds
        normal_fsr_imbalance_threshold=normal_fsr_imbalance,
        pusher_fsr_imbalance_threshold=pusher_fsr_imbalance,
        severe_fsr_imbalance_threshold=severe_fsr_imbalance,
        
        # Resistance detection
        resistance_force_threshold=resistance_force,
        resistance_angle_threshold=resistance_angle
    )


def validate_calibration_quality(calibration: CalibrationDataCreate) -> CalibrationValidationResult:
    """
    Validate calibration data quality and provide recommendations.
    """
    warnings = []
    recommendations = []
    quality_factors = []
    
    # Check pitch stability
    if calibration.pitch_std_dev > 3.0:
        warnings.append("High pitch variability during calibration - may indicate patient movement")
        quality_factors.append(0.6)
    elif calibration.pitch_std_dev > 1.5:
        warnings.append("Moderate pitch variability - acceptable but could be improved")
        quality_factors.append(0.8)
    else:
        quality_factors.append(1.0)
    
    # Check FSR stability
    if calibration.fsr_std_dev > 0.15:
        warnings.append("High FSR variability - may indicate unstable weight distribution")
        quality_factors.append(0.6)
    elif calibration.fsr_std_dev > 0.08:
        warnings.append("Moderate FSR variability - acceptable range")
        quality_factors.append(0.8)
    else:
        quality_factors.append(1.0)
    
    # Check FSR balance
    fsr_ratio = calibration.baseline_fsr_ratio
    if fsr_ratio < 0.3 or fsr_ratio > 0.7:
        warnings.append("Significant weight imbalance detected during calibration")
        recommendations.append("Consider recalibrating with more balanced posture")
        quality_factors.append(0.7)
    else:
        quality_factors.append(1.0)
    
    # Check calibration duration
    if calibration.calibration_duration < 20:
        warnings.append("Short calibration duration - may not capture full baseline variability")
        recommendations.append("Consider longer calibration period (30+ seconds)")
        quality_factors.append(0.8)
    else:
        quality_factors.append(1.0)
    
    # Calculate overall quality score
    quality_score = sum(quality_factors) / len(quality_factors) if quality_factors else 0.5
    
    # Add general recommendations
    if quality_score < 0.7:
        recommendations.append("Consider recalibrating for better baseline accuracy")
    if quality_score > 0.9:
        recommendations.append("Excellent calibration quality - thresholds will be highly accurate")
    
    baseline_stability = {
        "pitch_stability": 1.0 - min(1.0, calibration.pitch_std_dev / 5.0),
        "fsr_stability": 1.0 - min(1.0, calibration.fsr_std_dev / 0.2),
        "balance_stability": 1.0 - abs(fsr_ratio - 0.5) * 2.0
    }
    
    return CalibrationValidationResult(
        is_valid=quality_score >= 0.5,
        quality_score=quality_score,
        warnings=warnings,
        recommendations=recommendations,
        baseline_stability=baseline_stability
    )


def analyze_fsr_imbalance(current_fsr_left: int, current_fsr_right: int, 
                         calibration: CalibrationDataResponse,
                         adaptive_thresholds: AdaptiveThresholds) -> FSRImbalanceAnalysis:
    """
    Analyze FSR imbalance using calibrated ratios and adaptive thresholds.
    """
    # Calculate current ratio
    total_current = current_fsr_left + current_fsr_right
    current_ratio = current_fsr_right / total_current if total_current > 0 else 0.5
    
    # Calculate imbalance magnitude
    imbalance_magnitude = abs(current_ratio - calibration.baseline_fsr_ratio)
    
    # Determine direction
    if imbalance_magnitude < adaptive_thresholds.normal_fsr_imbalance_threshold:
        imbalance_direction = "balanced"
        severity_level = "normal"
        exceeds_threshold = False
    elif current_ratio > calibration.baseline_fsr_ratio:
        imbalance_direction = "right"
        if imbalance_magnitude >= adaptive_thresholds.severe_fsr_imbalance_threshold:
            severity_level = "severe"
            exceeds_threshold = True
        elif imbalance_magnitude >= adaptive_thresholds.pusher_fsr_imbalance_threshold:
            severity_level = "moderate"
            exceeds_threshold = True
        else:
            severity_level = "mild"
            exceeds_threshold = False
    else:
        imbalance_direction = "left"
        if imbalance_magnitude >= adaptive_thresholds.severe_fsr_imbalance_threshold:
            severity_level = "severe"
            exceeds_threshold = True
        elif imbalance_magnitude >= adaptive_thresholds.pusher_fsr_imbalance_threshold:
            severity_level = "moderate"
            exceeds_threshold = True
        else:
            severity_level = "mild"
            exceeds_threshold = False
    
    # Calculate confidence based on magnitude and stability
    confidence_level = min(1.0, imbalance_magnitude / adaptive_thresholds.severe_fsr_imbalance_threshold)
    
    return FSRImbalanceAnalysis(
        current_ratio=current_ratio,
        baseline_ratio=calibration.baseline_fsr_ratio,
        imbalance_magnitude=imbalance_magnitude,
        imbalance_direction=imbalance_direction,
        severity_level=severity_level,
        exceeds_threshold=exceeds_threshold,
        confidence_level=confidence_level
    )


def analyze_pitch_deviation(current_pitch: float, 
                           calibration: CalibrationDataResponse,
                           adaptive_thresholds: AdaptiveThresholds) -> PitchDeviationAnalysis:
    """
    Analyze pitch deviation from calibrated upright position using adaptive thresholds.
    """
    # Calculate deviation from calibrated baseline
    deviation_magnitude = abs(current_pitch - calibration.baseline_pitch)
    
    # Determine direction (relative to calibrated upright)
    pitch_diff = current_pitch - calibration.baseline_pitch
    if abs(pitch_diff) < 1.0:
        deviation_direction = "upright"
    elif pitch_diff > 0:
        deviation_direction = "right" if pitch_diff > 0 else "forward"  # Depends on sensor orientation
    else:
        deviation_direction = "left" if pitch_diff < 0 else "backward"  # Depends on sensor orientation
    
    # Classify severity using adaptive thresholds
    if deviation_magnitude < adaptive_thresholds.normal_pitch_threshold:
        severity_level = "normal"
        exceeds_threshold = False
    elif deviation_magnitude >= adaptive_thresholds.severe_pitch_threshold:
        severity_level = "severe"
        exceeds_threshold = True
    elif deviation_magnitude >= adaptive_thresholds.pusher_pitch_threshold:
        severity_level = "moderate"
        exceeds_threshold = True
    else:
        severity_level = "mild"
        exceeds_threshold = False
    
    # Calculate confidence based on deviation magnitude and threshold
    confidence_level = min(1.0, deviation_magnitude / adaptive_thresholds.severe_pitch_threshold)
    
    return PitchDeviationAnalysis(
        current_pitch=current_pitch,
        baseline_pitch=calibration.baseline_pitch,
        deviation_magnitude=deviation_magnitude,
        deviation_direction=deviation_direction,
        severity_level=severity_level,
        exceeds_threshold=exceeds_threshold,
        confidence_level=confidence_level
    )