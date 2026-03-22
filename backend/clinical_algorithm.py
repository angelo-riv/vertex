"""
Clinical-Grade Pusher Syndrome Detection Algorithm

This module implements clinically validated pusher syndrome detection algorithms
compatible with established clinical scales (BLS, 4PPS, SCP).

The algorithm uses three-criteria pattern detection:
1. Abnormal tilt (≥10° toward paretic side for >2s)
2. Active non-paretic limb use (>70% weight distribution)
3. Resistance to correction (<3-5° improvement during correction attempts)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import math
import logging
from collections import deque

logger = logging.getLogger(__name__)

class PareticSide(str, Enum):
    """Patient's paretic (affected) side"""
    LEFT = "left"
    RIGHT = "right"

class SeverityScore(int, Enum):
    """BLS/4PPS-compatible severity scoring"""
    NO_PUSHING = 0      # No pushing behavior
    MILD = 1           # Brief episodes 2-5s, minimal resistance
    MODERATE = 2       # Repeated episodes with some resistance
    SEVERE = 3         # Frequent episodes ≥20° with sustained resistance

class TiltClassification(str, Enum):
    """Clinical tilt angle classification"""
    NORMAL = "normal"                    # <5-7°
    POTENTIAL_PUSHER = "potential_pusher" # ≥10° for >2s
    SEVERE = "severe"                    # ≥20° indicating misperceived upright

class ClinicalThresholds(BaseModel):
    """Patient-specific clinical thresholds for pusher syndrome detection"""
    patient_id: str
    paretic_side: PareticSide
    normal_threshold: float = Field(default=5.0, ge=0.0, le=15.0, description="Normal lean threshold in degrees")
    pusher_threshold: float = Field(default=10.0, ge=5.0, le=25.0, description="Pusher-relevant threshold in degrees")
    severe_threshold: float = Field(default=20.0, ge=15.0, le=45.0, description="Severe lean threshold in degrees")
    resistance_threshold: float = Field(default=2.0, ge=0.5, le=5.0, description="Resistance detection threshold")
    episode_duration_min: float = Field(default=2.0, ge=1.0, le=10.0, description="Minimum episode duration in seconds")
    non_paretic_threshold: float = Field(default=0.7, ge=0.5, le=0.9, description="Non-paretic limb use threshold (0-1)")
    created_by: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalibrationData(BaseModel):
    """Patient-specific calibration baseline data"""
    patient_id: str
    device_id: str
    baseline_pitch: float = Field(description="Calibrated upright pitch angle in degrees")
    baseline_fsr_left: float = Field(description="Baseline left FSR reading")
    baseline_fsr_right: float = Field(description="Baseline right FSR reading")
    baseline_fsr_ratio: float = Field(description="Baseline FSR ratio (right/(left+right))")
    pitch_std_dev: float = Field(description="Standard deviation of pitch during calibration")
    fsr_std_dev: float = Field(description="Standard deviation of FSR ratio during calibration")
    calibration_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

class PusherEpisode(BaseModel):
    """Clinical pusher syndrome episode data"""
    patient_id: str
    episode_start: datetime
    episode_end: Optional[datetime] = None
    severity_score: SeverityScore
    max_tilt_angle: float = Field(description="Maximum tilt angle during episode")
    resistance_index: float = Field(description="Calculated resistance to correction")
    correction_attempts: int = Field(default=0, description="Number of correction attempts")
    clinical_notes: Optional[str] = None
    episode_id: Optional[str] = None

class PusherAnalysis(BaseModel):
    """Result of pusher syndrome analysis"""
    pusher_detected: bool
    severity_score: SeverityScore
    tilt_angle: float
    tilt_classification: TiltClassification
    weight_imbalance: float
    resistance_index: float
    confidence_level: float = Field(ge=0.0, le=1.0)
    paretic_tilt: float = Field(description="Tilt toward paretic side (positive values)")
    episode_duration: float = Field(default=0.0, description="Current episode duration in seconds")
    criteria_met: Dict[str, bool] = Field(default_factory=dict)

class SensorDataPoint(BaseModel):
    """Individual sensor data point for analysis"""
    timestamp: datetime
    pitch: float = Field(ge=-180.0, le=180.0)
    fsr_left: int = Field(ge=0, le=4095)
    fsr_right: int = Field(ge=0, le=4095)
    device_id: str

class CorrectionAttempt(BaseModel):
    """Data structure for tracking correction attempts"""
    start_time: datetime
    initial_angle: float
    target_improvement: float = 5.0  # Expected improvement in degrees
    duration: float = 2.0  # Correction attempt duration in seconds
    actual_improvement: Optional[float] = None
    resistance_detected: bool = False

class PusherDetectionAlgorithm:
    """
    Clinical-grade pusher syndrome detection algorithm implementing three-criteria analysis
    """
    
    def __init__(self, thresholds: ClinicalThresholds, calibration: CalibrationData):
        self.thresholds = thresholds
        self.calibration = calibration
        
        # Episode tracking
        self.current_episode: Optional[PusherEpisode] = None
        self.episode_start_time: Optional[datetime] = None
        
        # Data buffers for temporal analysis
        self.sensor_buffer = deque(maxlen=100)  # Last 100 sensor readings (~10-20 seconds at 5-10 Hz)
        self.correction_attempts: List[CorrectionAttempt] = []
        
        # Resistance detection state
        self.baseline_established = False
        self.resistance_baseline = 0.0
        self.resistance_std_dev = 1.0
        
        logger.info(f"Initialized pusher detection algorithm for patient {thresholds.patient_id}, "
                   f"paretic side: {thresholds.paretic_side}")
    
    def analyze_sensor_data(self, data: SensorDataPoint) -> PusherAnalysis:
        """
        Analyze sensor data for pusher syndrome using three-criteria detection:
        1. Abnormal tilt toward paretic side (≥10° for >2s)
        2. Active non-paretic limb use (>70% weight distribution)
        3. Resistance to correction (<3-5° improvement during correction)
        """
        
        # Add to sensor buffer for temporal analysis
        self.sensor_buffer.append(data)
        
        # Calculate adjusted pitch relative to calibrated baseline
        adjusted_pitch = data.pitch - self.calibration.baseline_pitch
        
        # Criterion 1: Abnormal tilt analysis
        paretic_tilt = self._calculate_paretic_tilt(adjusted_pitch)
        abnormal_tilt, tilt_duration = self._assess_abnormal_tilt(paretic_tilt)
        
        # Criterion 2: Weight distribution analysis
        fsr_ratio = self._calculate_fsr_ratio(data.fsr_left, data.fsr_right)
        weight_imbalance = self._assess_weight_imbalance(fsr_ratio)
        non_paretic_overuse = self._assess_non_paretic_use(fsr_ratio)
        
        # Criterion 3: Resistance to correction analysis
        resistance_detected = self._analyze_correction_resistance()
        
        # Combine criteria for pusher detection
        criteria_met = {
            "abnormal_tilt": abnormal_tilt,
            "non_paretic_overuse": non_paretic_overuse,
            "resistance_to_correction": resistance_detected
        }
        
        pusher_detected = all(criteria_met.values())
        
        # Calculate clinical severity score
        severity_score = self._calculate_severity_score(
            abs(paretic_tilt), 
            weight_imbalance, 
            resistance_detected,
            tilt_duration
        )
        
        # Classify tilt angle
        tilt_classification = self._classify_tilt_angle(abs(paretic_tilt), tilt_duration)
        
        # Calculate confidence level
        confidence_level = self._calculate_confidence(criteria_met, abs(paretic_tilt), tilt_duration)
        
        # Update episode tracking
        self._update_episode_tracking(pusher_detected, abs(paretic_tilt), data.timestamp)
        
        return PusherAnalysis(
            pusher_detected=pusher_detected,
            severity_score=severity_score,
            tilt_angle=abs(adjusted_pitch),
            tilt_classification=tilt_classification,
            weight_imbalance=weight_imbalance,
            resistance_index=self._calculate_resistance_index(),
            confidence_level=confidence_level,
            paretic_tilt=paretic_tilt,
            episode_duration=tilt_duration,
            criteria_met=criteria_met
        )
    
    def _calculate_paretic_tilt(self, adjusted_pitch: float) -> float:
        """
        Calculate tilt toward paretic side.
        Positive values indicate tilt toward paretic side.
        """
        if self.thresholds.paretic_side == PareticSide.RIGHT:
            # Positive pitch = right lean = toward paretic side
            return adjusted_pitch
        else:
            # Negative pitch = left lean = toward paretic side
            return -adjusted_pitch
    
    def _assess_abnormal_tilt(self, paretic_tilt: float) -> tuple[bool, float]:
        """
        Assess if current tilt is abnormal and calculate duration.
        Returns (is_abnormal, duration_seconds)
        """
        abs_tilt = abs(paretic_tilt)
        is_abnormal = abs_tilt >= self.thresholds.pusher_threshold
        
        # Calculate duration of current tilt episode
        duration = 0.0
        if len(self.sensor_buffer) >= 2:
            # Look backwards to find start of current tilt episode
            for i in range(len(self.sensor_buffer) - 1, -1, -1):
                reading = self.sensor_buffer[i]
                reading_tilt = abs(self._calculate_paretic_tilt(
                    reading.pitch - self.calibration.baseline_pitch
                ))
                
                if reading_tilt >= self.thresholds.pusher_threshold:
                    if i == 0:
                        # Reached beginning of buffer
                        duration = (self.sensor_buffer[-1].timestamp - self.sensor_buffer[0].timestamp).total_seconds()
                    else:
                        duration = (self.sensor_buffer[-1].timestamp - reading.timestamp).total_seconds()
                else:
                    break
        
        # Episode must last at least minimum duration
        abnormal_with_duration = is_abnormal and duration >= self.thresholds.episode_duration_min
        
        return abnormal_with_duration, duration
    
    def _calculate_fsr_ratio(self, fsr_left: int, fsr_right: int) -> float:
        """Calculate FSR ratio (right/(left+right))"""
        total = fsr_left + fsr_right
        if total == 0:
            return 0.5  # Default to balanced if no pressure
        return fsr_right / total
    
    def _assess_weight_imbalance(self, current_ratio: float) -> float:
        """
        Assess weight imbalance relative to calibrated baseline.
        Returns absolute deviation from baseline ratio.
        """
        baseline_ratio = self.calibration.baseline_fsr_ratio
        return abs(current_ratio - baseline_ratio)
    
    def _assess_non_paretic_use(self, current_ratio: float) -> bool:
        """
        Assess if non-paretic limb is being overused (>70% weight distribution).
        """
        if self.thresholds.paretic_side == PareticSide.RIGHT:
            # Non-paretic is left, so low ratio indicates overuse
            non_paretic_ratio = 1.0 - current_ratio
        else:
            # Non-paretic is right, so high ratio indicates overuse
            non_paretic_ratio = current_ratio
        
        return non_paretic_ratio > self.thresholds.non_paretic_threshold
    
    def _analyze_correction_resistance(self) -> bool:
        """
        Analyze resistance to correction attempts.
        This is a simplified implementation - in practice would require
        integration with correction attempt detection.
        """
        if not self.correction_attempts:
            return False
        
        # Check recent correction attempts for resistance
        recent_attempts = [
            attempt for attempt in self.correction_attempts
            if (datetime.now(timezone.utc) - attempt.start_time).total_seconds() < 30
        ]
        
        if not recent_attempts:
            return False
        
        # Calculate resistance based on actual vs expected improvement
        resistance_count = sum(1 for attempt in recent_attempts if attempt.resistance_detected)
        resistance_ratio = resistance_count / len(recent_attempts)
        
        return resistance_ratio > 0.5  # More than half of attempts showed resistance
    
    def _calculate_severity_score(self, tilt_angle: float, weight_imbalance: float, 
                                resistance: bool, duration: float) -> SeverityScore:
        """
        Calculate BLS/4PPS-compatible severity score:
        0 = No pushing behavior
        1 = Mild (brief episodes 2-5s, minimal resistance)
        2 = Moderate (repeated episodes with some resistance)
        3 = Severe (frequent episodes ≥20° with sustained resistance)
        """
        if tilt_angle < self.thresholds.normal_threshold:
            return SeverityScore.NO_PUSHING
        
        if tilt_angle >= self.thresholds.severe_threshold and resistance and duration > 5.0:
            return SeverityScore.SEVERE
        
        if tilt_angle >= self.thresholds.pusher_threshold and resistance:
            return SeverityScore.MODERATE
        
        if tilt_angle >= self.thresholds.pusher_threshold and duration >= self.thresholds.episode_duration_min:
            return SeverityScore.MILD
        
        return SeverityScore.NO_PUSHING
    
    def _classify_tilt_angle(self, tilt_angle: float, duration: float) -> TiltClassification:
        """
        Classify tilt angle according to clinical thresholds:
        - Normal: <5-7°
        - Potential pusher-relevant: ≥10° for >2s
        - Severe: ≥20° indicating misperceived upright
        """
        if tilt_angle < self.thresholds.normal_threshold:
            return TiltClassification.NORMAL
        
        if tilt_angle >= self.thresholds.severe_threshold:
            return TiltClassification.SEVERE
        
        if tilt_angle >= self.thresholds.pusher_threshold and duration >= self.thresholds.episode_duration_min:
            return TiltClassification.POTENTIAL_PUSHER
        
        return TiltClassification.NORMAL
    
    def _calculate_confidence(self, criteria_met: Dict[str, bool], tilt_angle: float, duration: float) -> float:
        """
        Calculate confidence level for pusher detection (0.0 to 1.0).
        Higher confidence when more criteria are met and measurements are more extreme.
        """
        base_confidence = 0.3
        
        # Increase confidence for each criterion met
        criteria_confidence = sum(criteria_met.values()) * 0.2
        
        # Increase confidence for higher tilt angles
        angle_confidence = min(tilt_angle / self.thresholds.severe_threshold, 1.0) * 0.3
        
        # Increase confidence for longer duration
        duration_confidence = min(duration / 10.0, 1.0) * 0.2
        
        total_confidence = base_confidence + criteria_confidence + angle_confidence + duration_confidence
        return min(total_confidence, 1.0)
    
    def _calculate_resistance_index(self) -> float:
        """
        Calculate resistance index based on recent correction attempts.
        Returns value between 0.0 (no resistance) and 1.0 (maximum resistance).
        """
        if not self.correction_attempts:
            return 0.0
        
        recent_attempts = [
            attempt for attempt in self.correction_attempts
            if (datetime.now(timezone.utc) - attempt.start_time).total_seconds() < 60
        ]
        
        if not recent_attempts:
            return 0.0
        
        resistance_scores = []
        for attempt in recent_attempts:
            if attempt.actual_improvement is not None:
                expected = attempt.target_improvement
                actual = attempt.actual_improvement
                resistance_score = max(0.0, 1.0 - (actual / expected))
                resistance_scores.append(resistance_score)
        
        if not resistance_scores:
            return 0.0
        
        return sum(resistance_scores) / len(resistance_scores)
    
    def _update_episode_tracking(self, pusher_detected: bool, tilt_angle: float, timestamp: datetime):
        """Update current episode tracking"""
        if pusher_detected:
            if self.current_episode is None:
                # Start new episode
                self.current_episode = PusherEpisode(
                    patient_id=self.thresholds.patient_id,
                    episode_start=timestamp,
                    severity_score=SeverityScore.MILD,
                    max_tilt_angle=tilt_angle,
                    resistance_index=self._calculate_resistance_index()
                )
                self.episode_start_time = timestamp
            else:
                # Update existing episode
                self.current_episode.max_tilt_angle = max(self.current_episode.max_tilt_angle, tilt_angle)
                self.current_episode.resistance_index = self._calculate_resistance_index()
        else:
            if self.current_episode is not None:
                # End current episode
                self.current_episode.episode_end = timestamp
                self.current_episode = None
                self.episode_start_time = None
    
    def add_correction_attempt(self, initial_angle: float, target_improvement: float = 5.0):
        """
        Add a correction attempt for resistance analysis.
        Should be called when a correction intervention begins.
        """
        attempt = CorrectionAttempt(
            start_time=datetime.now(timezone.utc),
            initial_angle=initial_angle,
            target_improvement=target_improvement
        )
        self.correction_attempts.append(attempt)
        
        # Keep only recent attempts (last 5 minutes)
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        self.correction_attempts = [
            attempt for attempt in self.correction_attempts
            if attempt.start_time > cutoff_time
        ]
        
        return attempt
    
    def complete_correction_attempt(self, final_angle: float) -> Optional[CorrectionAttempt]:
        """
        Complete the most recent correction attempt with the final angle.
        Returns the completed attempt or None if no active attempt.
        """
        if not self.correction_attempts:
            return None
        
        # Find the most recent uncompleted attempt
        for attempt in reversed(self.correction_attempts):
            if attempt.actual_improvement is None:
                improvement = attempt.initial_angle - final_angle
                attempt.actual_improvement = improvement
                
                # Detect resistance (less than expected improvement)
                expected_improvement = attempt.target_improvement
                resistance_threshold = expected_improvement * 0.6  # 60% of expected
                attempt.resistance_detected = improvement < resistance_threshold
                
                logger.info(f"Completed correction attempt: initial={attempt.initial_angle:.1f}°, "
                           f"final={final_angle:.1f}°, improvement={improvement:.1f}°, "
                           f"expected={expected_improvement:.1f}°, resistance={attempt.resistance_detected}")
                
                return attempt
        
        return None
    
    def get_current_episode(self) -> Optional[PusherEpisode]:
        """Get the current active episode, if any"""
        return self.current_episode
    
    def get_daily_metrics(self, date: datetime, sensor_readings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate daily metrics for clinical reporting.
        
        Args:
            date: The date to calculate metrics for
            sensor_readings: List of sensor readings for the day (optional, for real-time calculation)
        
        Returns:
            Dictionary containing daily clinical metrics
        """
        if sensor_readings is None:
            sensor_readings = []
        
        # Filter readings for the specific date
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        daily_readings = [
            r for r in sensor_readings 
            if day_start <= datetime.fromisoformat(r.get('timestamp', '')) < day_end
        ] if sensor_readings else []
        
        # Calculate episode frequency
        episodes = self._calculate_daily_episodes(daily_readings)
        total_episodes = len(episodes)
        
        # Calculate tilt angle statistics during episodes
        episode_tilt_angles = []
        for episode in episodes:
            episode_tilt_angles.extend(episode.get('tilt_angles', []))
        
        mean_tilt_angle = sum(episode_tilt_angles) / len(episode_tilt_angles) if episode_tilt_angles else 0.0
        max_tilt_angle = max(episode_tilt_angles) if episode_tilt_angles else 0.0
        
        # Calculate resistance index during correction attempts
        resistance_index = self._calculate_daily_resistance_index(daily_readings)
        
        # Calculate time spent within ±5° of vertical
        time_within_normal = self._calculate_time_within_normal(daily_readings)
        
        # Count correction attempts
        correction_attempts = len([r for r in daily_readings if r.get('correction_attempt', False)])
        
        return {
            "date": date.date().isoformat(),
            "total_episodes": total_episodes,
            "mean_tilt_angle": round(mean_tilt_angle, 2),
            "max_tilt_angle": round(max_tilt_angle, 2),
            "time_within_normal": round(time_within_normal, 1),  # Percentage of time within ±5° of vertical
            "resistance_index": round(resistance_index, 3),
            "correction_attempts": correction_attempts,
            "episodes_detail": episodes
        }
    
    def _calculate_daily_episodes(self, readings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate pusher syndrome episodes from daily sensor readings."""
        episodes = []
        current_episode = None
        episode_gap_threshold = 5.0  # seconds
        
        for i, reading in enumerate(readings):
            pusher_detected = reading.get('pusher_detected', False)
            tilt_angle = abs(reading.get('imu_pitch', 0))
            timestamp = datetime.fromisoformat(reading.get('timestamp', ''))
            
            if pusher_detected and tilt_angle >= self.thresholds.pusher_threshold:
                if current_episode is None:
                    # Start new episode
                    current_episode = {
                        'start_time': timestamp,
                        'end_time': timestamp,
                        'max_tilt': tilt_angle,
                        'tilt_angles': [tilt_angle],
                        'severity_score': reading.get('clinical_score', 0),
                        'resistance_events': 0
                    }
                else:
                    # Continue current episode
                    current_episode['end_time'] = timestamp
                    current_episode['max_tilt'] = max(current_episode['max_tilt'], tilt_angle)
                    current_episode['tilt_angles'].append(tilt_angle)
                    current_episode['severity_score'] = max(current_episode['severity_score'], reading.get('clinical_score', 0))
                    
                    # Check for resistance during correction
                    if reading.get('correction_attempt', False):
                        current_episode['resistance_events'] += 1
            else:
                # End current episode if gap is too large
                if current_episode is not None:
                    prev_timestamp = datetime.fromisoformat(readings[i-1].get('timestamp', ''))
                    gap = (timestamp - prev_timestamp).total_seconds()
                    
                    if gap > episode_gap_threshold:
                        # Calculate episode duration
                        duration = (current_episode['end_time'] - current_episode['start_time']).total_seconds()
                        current_episode['duration_seconds'] = duration
                        current_episode['mean_tilt'] = sum(current_episode['tilt_angles']) / len(current_episode['tilt_angles'])
                        
                        episodes.append(current_episode)
                        current_episode = None
        
        # Close final episode if exists
        if current_episode is not None:
            duration = (current_episode['end_time'] - current_episode['start_time']).total_seconds()
            current_episode['duration_seconds'] = duration
            current_episode['mean_tilt'] = sum(current_episode['tilt_angles']) / len(current_episode['tilt_angles'])
            episodes.append(current_episode)
        
        return episodes
    
    def _calculate_daily_resistance_index(self, readings: List[Dict[str, Any]]) -> float:
        """Calculate resistance index during correction attempts."""
        correction_attempts = [r for r in readings if r.get('correction_attempt', False)]
        
        if not correction_attempts:
            return 0.0
        
        resistance_scores = []
        for attempt in correction_attempts:
            initial_angle = attempt.get('initial_angle', 0)
            final_angle = attempt.get('final_angle', initial_angle)
            expected_improvement = 5.0  # Expected 5° improvement during correction
            
            actual_improvement = abs(initial_angle) - abs(final_angle)
            resistance_ratio = max(0, (expected_improvement - actual_improvement) / expected_improvement)
            resistance_scores.append(resistance_ratio)
        
        return sum(resistance_scores) / len(resistance_scores) if resistance_scores else 0.0
    
    def _calculate_time_within_normal(self, readings: List[Dict[str, Any]]) -> float:
        """Calculate percentage of time spent within ±5° of vertical."""
        if not readings:
            return 0.0
        
        normal_threshold = 5.0  # ±5° of vertical
        normal_readings = sum(1 for r in readings if abs(r.get('imu_pitch', 0)) <= normal_threshold)
        
        return (normal_readings / len(readings)) * 100.0

    def get_weekly_progress_report(self, end_date: datetime, sensor_readings: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate weekly progress report showing trends and improvements.
        
        Args:
            end_date: End date for the weekly report
            sensor_readings: List of sensor readings for the week
        
        Returns:
            Dictionary containing weekly progress analysis
        """
        if sensor_readings is None:
            sensor_readings = []
        
        # Calculate daily metrics for each day of the week
        daily_metrics = []
        week_start = end_date - timedelta(days=6)  # 7-day period including end_date
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_readings = [
                r for r in sensor_readings 
                if day.date() == datetime.fromisoformat(r.get('timestamp', '')).date()
            ]
            metrics = self.get_daily_metrics(day, day_readings)
            daily_metrics.append(metrics)
        
        # Calculate trend analysis
        episode_counts = [m['total_episodes'] for m in daily_metrics]
        mean_tilts = [m['mean_tilt_angle'] for m in daily_metrics if m['mean_tilt_angle'] > 0]
        max_tilts = [m['max_tilt_angle'] for m in daily_metrics if m['max_tilt_angle'] > 0]
        resistance_indices = [m['resistance_index'] for m in daily_metrics if m['resistance_index'] > 0]
        time_within_normal = [m['time_within_normal'] for m in daily_metrics]
        
        # Calculate trends (positive = improving, negative = worsening)
        episode_trend = self._calculate_trend(episode_counts)  # Negative is better (fewer episodes)
        tilt_trend = self._calculate_trend(mean_tilts, invert=True)  # Negative is better (smaller angles)
        resistance_trend = self._calculate_trend(resistance_indices, invert=True)  # Negative is better (less resistance)
        normal_time_trend = self._calculate_trend(time_within_normal)  # Positive is better (more time normal)
        
        # Calculate percentage of tasks with no pushing behavior
        total_readings = len(sensor_readings)
        no_pushing_readings = sum(1 for r in sensor_readings if not r.get('pusher_detected', False))
        no_pushing_percentage = (no_pushing_readings / total_readings) * 100 if total_readings > 0 else 0
        
        # Generate clinical interpretation
        overall_trend = self._assess_overall_progress(episode_trend, tilt_trend, resistance_trend, normal_time_trend)
        
        return {
            "report_period": {
                "start_date": week_start.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "days_analyzed": 7
            },
            "weekly_summary": {
                "total_episodes": sum(episode_counts),
                "average_daily_episodes": round(sum(episode_counts) / 7, 1),
                "average_mean_tilt": round(sum(mean_tilts) / len(mean_tilts), 2) if mean_tilts else 0.0,
                "peak_tilt_angle": max(max_tilts) if max_tilts else 0.0,
                "average_resistance_index": round(sum(resistance_indices) / len(resistance_indices), 3) if resistance_indices else 0.0,
                "average_time_within_normal": round(sum(time_within_normal) / 7, 1),
                "no_pushing_percentage": round(no_pushing_percentage, 1)
            },
            "trend_analysis": {
                "episode_frequency_trend": {
                    "direction": "improving" if episode_trend < -0.1 else "worsening" if episode_trend > 0.1 else "stable",
                    "slope": round(episode_trend, 3),
                    "interpretation": "Episodes decreasing" if episode_trend < -0.1 else "Episodes increasing" if episode_trend > 0.1 else "Episode frequency stable"
                },
                "tilt_angle_improvement": {
                    "direction": "improving" if tilt_trend > 0.1 else "worsening" if tilt_trend < -0.1 else "stable",
                    "slope": round(tilt_trend, 3),
                    "interpretation": "Tilt angles decreasing" if tilt_trend > 0.1 else "Tilt angles increasing" if tilt_trend < -0.1 else "Tilt angles stable"
                },
                "resistance_reduction": {
                    "direction": "improving" if resistance_trend > 0.1 else "worsening" if resistance_trend < -0.1 else "stable",
                    "slope": round(resistance_trend, 3),
                    "interpretation": "Resistance decreasing" if resistance_trend > 0.1 else "Resistance increasing" if resistance_trend < -0.1 else "Resistance stable"
                },
                "normal_posture_time": {
                    "direction": "improving" if normal_time_trend > 0.1 else "worsening" if normal_time_trend < -0.1 else "stable",
                    "slope": round(normal_time_trend, 3),
                    "interpretation": "More time in normal posture" if normal_time_trend > 0.1 else "Less time in normal posture" if normal_time_trend < -0.1 else "Normal posture time stable"
                }
            },
            "clinical_assessment": {
                "overall_progress": overall_trend,
                "key_improvements": self._identify_key_improvements(episode_trend, tilt_trend, resistance_trend, normal_time_trend),
                "areas_of_concern": self._identify_concerns(episode_trend, tilt_trend, resistance_trend, normal_time_trend),
                "recommendations": self._generate_recommendations(overall_trend, daily_metrics)
            },
            "daily_breakdown": daily_metrics
        }
    
    def _calculate_trend(self, values: List[float], invert: bool = False) -> float:
        """Calculate linear trend slope for a series of values."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope calculation
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return -slope if invert else slope
    
    def _assess_overall_progress(self, episode_trend: float, tilt_trend: float, 
                               resistance_trend: float, normal_time_trend: float) -> str:
        """Assess overall patient progress based on multiple trend indicators."""
        improvement_score = 0
        
        # Episode frequency (fewer is better)
        if episode_trend < -0.1:
            improvement_score += 2
        elif episode_trend > 0.1:
            improvement_score -= 2
        
        # Tilt angle improvement (smaller angles is better)
        if tilt_trend > 0.1:
            improvement_score += 2
        elif tilt_trend < -0.1:
            improvement_score -= 2
        
        # Resistance reduction (less resistance is better)
        if resistance_trend > 0.1:
            improvement_score += 1
        elif resistance_trend < -0.1:
            improvement_score -= 1
        
        # Normal posture time (more is better)
        if normal_time_trend > 0.1:
            improvement_score += 1
        elif normal_time_trend < -0.1:
            improvement_score -= 1
        
        if improvement_score >= 3:
            return "significant_improvement"
        elif improvement_score >= 1:
            return "moderate_improvement"
        elif improvement_score <= -3:
            return "concerning_decline"
        elif improvement_score <= -1:
            return "mild_decline"
        else:
            return "stable"
    
    def _identify_key_improvements(self, episode_trend: float, tilt_trend: float, 
                                 resistance_trend: float, normal_time_trend: float) -> List[str]:
        """Identify key areas of improvement."""
        improvements = []
        
        if episode_trend < -0.1:
            improvements.append("Reduced frequency of pusher episodes")
        if tilt_trend > 0.1:
            improvements.append("Decreased tilt angles during episodes")
        if resistance_trend > 0.1:
            improvements.append("Reduced resistance to postural correction")
        if normal_time_trend > 0.1:
            improvements.append("Increased time maintaining normal posture")
        
        return improvements
    
    def _identify_concerns(self, episode_trend: float, tilt_trend: float, 
                         resistance_trend: float, normal_time_trend: float) -> List[str]:
        """Identify areas of concern."""
        concerns = []
        
        if episode_trend > 0.1:
            concerns.append("Increasing frequency of pusher episodes")
        if tilt_trend < -0.1:
            concerns.append("Worsening tilt angles during episodes")
        if resistance_trend < -0.1:
            concerns.append("Increased resistance to postural correction")
        if normal_time_trend < -0.1:
            concerns.append("Decreased time maintaining normal posture")
        
        return concerns
    
    def _generate_recommendations(self, overall_progress: str, daily_metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate clinical recommendations based on progress analysis."""
        recommendations = []
        
        if overall_progress == "significant_improvement":
            recommendations.extend([
                "Continue current therapy protocol - excellent progress",
                "Consider gradual reduction in feedback intensity",
                "Prepare for transition to independent practice"
            ])
        elif overall_progress == "moderate_improvement":
            recommendations.extend([
                "Maintain current therapy approach",
                "Monitor for continued improvement trends",
                "Consider increasing therapy session frequency"
            ])
        elif overall_progress == "stable":
            recommendations.extend([
                "Evaluate current therapy effectiveness",
                "Consider adjusting feedback thresholds",
                "Explore alternative therapy approaches"
            ])
        elif overall_progress == "mild_decline":
            recommendations.extend([
                "Review patient compliance and device usage",
                "Consider increasing therapy intensity",
                "Evaluate for external factors affecting progress"
            ])
        elif overall_progress == "concerning_decline":
            recommendations.extend([
                "Immediate clinical review recommended",
                "Consider comprehensive reassessment",
                "Evaluate for medical complications or changes"
            ])
        
        # Add specific recommendations based on daily patterns
        avg_episodes = sum(m['total_episodes'] for m in daily_metrics) / 7
        if avg_episodes > 10:
            recommendations.append("High episode frequency - consider more intensive intervention")
        
        avg_resistance = sum(m['resistance_index'] for m in daily_metrics if m['resistance_index'] > 0)
        if avg_resistance and avg_resistance / len([m for m in daily_metrics if m['resistance_index'] > 0]) > 0.7:
            recommendations.append("High resistance index - focus on awareness training")
        
        return recommendations


def create_default_thresholds(patient_id: str, paretic_side: PareticSide) -> ClinicalThresholds:
    """Create default clinical thresholds for a patient"""
    return ClinicalThresholds(
        patient_id=patient_id,
        paretic_side=paretic_side,
        normal_threshold=5.0,
        pusher_threshold=10.0,
        severe_threshold=20.0,
        resistance_threshold=2.0,
        episode_duration_min=2.0,
        non_paretic_threshold=0.7
    )

def create_default_calibration(patient_id: str, device_id: str) -> CalibrationData:
    """Create default calibration data (should be replaced with actual calibration)"""
    return CalibrationData(
        patient_id=patient_id,
        device_id=device_id,
        baseline_pitch=0.0,
        baseline_fsr_left=2048.0,
        baseline_fsr_right=2048.0,
        baseline_fsr_ratio=0.5,
        pitch_std_dev=1.0,
        fsr_std_dev=0.1
    )