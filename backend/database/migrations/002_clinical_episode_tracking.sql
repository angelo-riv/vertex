-- Migration: Clinical Episode Tracking Tables
-- Date: 2024-01-XX
-- Description: Create comprehensive clinical episode tracking tables for pusher syndrome detection and analytics
-- Task: 8.1 Create clinical episode tracking tables
-- Requirements: 14.3, 15.6, 17.6, 18.1

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PUSHER EPISODES TABLE - Clinical episode tracking with severity scoring
-- ============================================================================
CREATE TABLE IF NOT EXISTS pusher_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
    session_id UUID REFERENCES monitoring_sessions(id) ON DELETE CASCADE,
    device_id VARCHAR NOT NULL,
    episode_start TIMESTAMP WITH TIME ZONE NOT NULL,
    episode_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Clinical Severity Scoring (BLS/4PPS compatible)
    severity_score INTEGER CHECK (severity_score >= 0 AND severity_score <= 3) NOT NULL,
    -- 0=No pushing, 1=Mild (2-5s), 2=Moderate (repeated with resistance), 3=Severe (≥20° with sustained resistance)
    
    -- Tilt and Resistance Metrics
    max_tilt_angle FLOAT NOT NULL,
    mean_tilt_angle FLOAT,
    tilt_direction VARCHAR CHECK (tilt_direction IN ('left', 'right', 'bilateral')) NOT NULL,
    resistance_index FLOAT, -- Calculated resistance to correction attempts
    correction_attempts INTEGER DEFAULT 0,
    correction_success_rate FLOAT, -- Percentage of successful corrections
    
    -- Episode Duration and Frequency
    episode_duration_seconds FLOAT NOT NULL,
    time_to_correction FLOAT, -- Time from detection to successful correction
    
    -- Weight Distribution Analysis
    initial_weight_ratio FLOAT, -- FSR left/right ratio at episode start
    final_weight_ratio FLOAT, -- FSR left/right ratio at episode end
    weight_shift_magnitude FLOAT, -- Change in weight distribution
    
    -- Clinical Context
    activity_context VARCHAR, -- What the patient was doing during episode
    clinical_notes TEXT,
    therapist_id VARCHAR, -- ID of supervising therapist
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- CLINICAL THRESHOLDS TABLE - Patient-specific parameters
-- ============================================================================
CREATE TABLE IF NOT EXISTS clinical_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
    
    -- Patient-Specific Configuration
    paretic_side VARCHAR CHECK (paretic_side IN ('left', 'right')) NOT NULL,
    stroke_severity INTEGER CHECK (stroke_severity >= 1 AND stroke_severity <= 5),
    
    -- Tilt Angle Thresholds (degrees)
    normal_threshold FLOAT DEFAULT 5.0 CHECK (normal_threshold >= 0.0 AND normal_threshold <= 15.0),
    pusher_threshold FLOAT DEFAULT 10.0 CHECK (pusher_threshold >= 5.0 AND pusher_threshold <= 25.0),
    severe_threshold FLOAT DEFAULT 20.0 CHECK (severe_threshold >= 15.0 AND severe_threshold <= 45.0),
    
    -- Resistance and Correction Parameters
    resistance_threshold FLOAT DEFAULT 2.0 CHECK (resistance_threshold >= 0.5 AND resistance_threshold <= 5.0),
    correction_time_window FLOAT DEFAULT 2.0 CHECK (correction_time_window >= 1.0 AND correction_time_window <= 5.0),
    
    -- Episode Detection Parameters
    episode_duration_min FLOAT DEFAULT 2.0 CHECK (episode_duration_min >= 1.0 AND episode_duration_min <= 10.0),
    episode_gap_max FLOAT DEFAULT 5.0 CHECK (episode_gap_max >= 2.0 AND episode_gap_max <= 15.0),
    
    -- Weight Distribution Thresholds
    non_paretic_threshold FLOAT DEFAULT 0.7 CHECK (non_paretic_threshold >= 0.5 AND non_paretic_threshold <= 0.9),
    weight_imbalance_threshold FLOAT DEFAULT 0.2 CHECK (weight_imbalance_threshold >= 0.1 AND weight_imbalance_threshold <= 0.4),
    
    -- Clinical Authorization
    created_by VARCHAR NOT NULL, -- Therapist ID or username
    approved_by VARCHAR, -- Supervising clinician approval
    therapist_notes TEXT,
    clinical_rationale TEXT, -- Justification for threshold values
    
    -- Version Control
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    effective_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expiry_date TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ESP32 DEVICES TABLE - Device registry and connection tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS esp32_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR UNIQUE NOT NULL,
    
    -- Device Information
    device_name VARCHAR,
    device_type VARCHAR DEFAULT 'ESP32_Wearable',
    firmware_version VARCHAR,
    hardware_revision VARCHAR,
    mac_address VARCHAR,
    
    -- Network Configuration
    ip_address INET,
    network_ssid VARCHAR,
    signal_strength INTEGER, -- WiFi signal strength in dBm
    
    -- Connection Status
    connection_status VARCHAR DEFAULT 'disconnected' CHECK (connection_status IN ('connected', 'disconnected', 'error', 'calibrating')),
    last_seen TIMESTAMP WITH TIME ZONE,
    last_data_timestamp TIMESTAMP WITH TIME ZONE,
    connection_quality VARCHAR DEFAULT 'unknown' CHECK (connection_quality IN ('excellent', 'good', 'poor', 'unknown')),
    
    -- Device Assignment
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    assigned_date TIMESTAMP WITH TIME ZONE,
    assignment_notes TEXT,
    
    -- Battery and Health Monitoring
    battery_level INTEGER CHECK (battery_level >= 0 AND battery_level <= 100),
    sensor_status JSONB, -- Status of individual sensors (IMU, FSR1, FSR2)
    calibration_status VARCHAR DEFAULT 'not_calibrated' CHECK (calibration_status IN ('not_calibrated', 'calibrating', 'calibrated', 'expired')),
    
    -- Usage Statistics
    total_uptime_hours FLOAT DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    last_maintenance_date TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- ENHANCED DEVICE CALIBRATIONS TABLE - FSR baselines and statistical parameters
-- ============================================================================
-- First, add new columns to existing device_calibrations table
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS device_id VARCHAR;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS calibration_type VARCHAR DEFAULT 'manual' CHECK (calibration_type IN ('manual', 'automatic', 'assisted'));

-- FSR Baseline Data
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_left FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_right FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_ratio FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_sum FLOAT;

-- Statistical Parameters
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS pitch_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS roll_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS fsr_left_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS fsr_right_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS fsr_ratio_std_dev FLOAT;

-- Calibration Process Data
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS calibration_duration INTEGER DEFAULT 30; -- seconds
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS sample_count INTEGER; -- Number of samples collected
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS sample_rate FLOAT; -- Hz
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS calibration_quality FLOAT; -- 0.0-1.0 quality score

-- Environmental Context
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS calibration_position VARCHAR; -- 'sitting', 'standing', 'lying'
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS environmental_notes TEXT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS therapist_supervised BOOLEAN DEFAULT FALSE;

-- Validation and Approval
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS validation_status VARCHAR DEFAULT 'pending' CHECK (validation_status IN ('pending', 'approved', 'rejected', 'expired'));
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS validated_by VARCHAR; -- Therapist ID
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS validation_notes TEXT;

-- Update existing columns with better constraints
ALTER TABLE device_calibrations ALTER COLUMN baseline_pitch SET NOT NULL;
ALTER TABLE device_calibrations ADD CONSTRAINT check_baseline_pitch_range CHECK (baseline_pitch >= -45.0 AND baseline_pitch <= 45.0);

-- ============================================================================
-- ENHANCED SENSOR READINGS TABLE - Clinical data integration
-- ============================================================================
-- Add clinical analysis columns to existing sensor_readings table
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS device_id VARCHAR;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS pusher_detected BOOLEAN DEFAULT FALSE;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS confidence_level FLOAT CHECK (confidence_level >= 0.0 AND confidence_level <= 1.0);
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS clinical_score INTEGER CHECK (clinical_score >= 0 AND clinical_score <= 3);
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS episode_id UUID;

-- Additional clinical analysis fields
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS tilt_direction VARCHAR CHECK (tilt_direction IN ('left', 'right', 'center'));
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS weight_ratio FLOAT; -- FSR left/(left+right)
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS resistance_detected BOOLEAN DEFAULT FALSE;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS correction_attempt BOOLEAN DEFAULT FALSE;

-- Data quality indicators
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS data_quality FLOAT CHECK (data_quality >= 0.0 AND data_quality <= 1.0);
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS sensor_errors JSONB; -- Error flags for individual sensors

-- Add foreign key constraint for episode tracking
ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS fk_sensor_readings_episode 
    FOREIGN KEY (episode_id) REFERENCES pusher_episodes(id) ON DELETE SET NULL;

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Pusher Episodes Indexes
CREATE INDEX IF NOT EXISTS idx_pusher_episodes_patient_date ON pusher_episodes(patient_id, episode_start DESC);
CREATE INDEX IF NOT EXISTS idx_pusher_episodes_severity ON pusher_episodes(severity_score, episode_start DESC);
CREATE INDEX IF NOT EXISTS idx_pusher_episodes_device ON pusher_episodes(device_id, episode_start DESC);
CREATE INDEX IF NOT EXISTS idx_pusher_episodes_session ON pusher_episodes(session_id, episode_start DESC);

-- Clinical Thresholds Indexes
CREATE INDEX IF NOT EXISTS idx_clinical_thresholds_patient_active ON clinical_thresholds(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_clinical_thresholds_version ON clinical_thresholds(patient_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_clinical_thresholds_effective ON clinical_thresholds(effective_date, expiry_date);

-- ESP32 Devices Indexes
CREATE INDEX IF NOT EXISTS idx_esp32_devices_status ON esp32_devices(connection_status, last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_esp32_devices_patient ON esp32_devices(patient_id, assigned_date DESC);
CREATE INDEX IF NOT EXISTS idx_esp32_devices_device_id ON esp32_devices(device_id);

-- Enhanced Calibrations Indexes
CREATE INDEX IF NOT EXISTS idx_device_calibrations_device_active ON device_calibrations(device_id, is_active);
CREATE INDEX IF NOT EXISTS idx_device_calibrations_validation ON device_calibrations(validation_status, calibration_date DESC);

-- Enhanced Sensor Readings Indexes
CREATE INDEX IF NOT EXISTS idx_sensor_readings_episode ON sensor_readings(episode_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_pusher ON sensor_readings(pusher_detected, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_device_time ON sensor_readings(device_id, timestamp DESC);

-- ============================================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on new tables
ALTER TABLE pusher_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_thresholds ENABLE ROW LEVEL SECURITY;
ALTER TABLE esp32_devices ENABLE ROW LEVEL SECURITY;

-- Pusher Episodes Policies
CREATE POLICY "Patients can view own pusher episodes" ON pusher_episodes
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Patients can manage own pusher episodes" ON pusher_episodes
    FOR ALL USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Therapists can manage patient episodes" ON pusher_episodes
    FOR ALL USING (
        therapist_id = auth.uid()::text
        OR patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- Clinical Thresholds Policies
CREATE POLICY "Patients can view own clinical thresholds" ON clinical_thresholds
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Therapists can manage clinical thresholds" ON clinical_thresholds
    FOR ALL USING (
        created_by = auth.uid()::text
        OR approved_by = auth.uid()::text
        OR patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- ESP32 Devices Policies (allow service access for device management)
CREATE POLICY "Service can manage ESP32 devices" ON esp32_devices
    FOR ALL USING (true);

CREATE POLICY "Patients can view assigned devices" ON esp32_devices
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_pusher_episodes_updated_at 
    BEFORE UPDATE ON pusher_episodes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinical_thresholds_updated_at 
    BEFORE UPDATE ON clinical_thresholds 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_esp32_devices_updated_at 
    BEFORE UPDATE ON esp32_devices 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate episode statistics
CREATE OR REPLACE FUNCTION calculate_episode_statistics()
RETURNS TRIGGER AS $
BEGIN
    -- Calculate episode duration
    NEW.episode_duration_seconds = EXTRACT(EPOCH FROM (NEW.episode_end - NEW.episode_start));
    
    -- Calculate correction success rate if attempts were made
    IF NEW.correction_attempts > 0 THEN
        NEW.correction_success_rate = COALESCE(NEW.correction_success_rate, 0.0);
    END IF;
    
    -- Calculate weight shift magnitude if both ratios are available
    IF NEW.initial_weight_ratio IS NOT NULL AND NEW.final_weight_ratio IS NOT NULL THEN
        NEW.weight_shift_magnitude = ABS(NEW.final_weight_ratio - NEW.initial_weight_ratio);
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Trigger to automatically calculate episode statistics
CREATE TRIGGER calculate_pusher_episode_stats
    BEFORE INSERT OR UPDATE ON pusher_episodes
    FOR EACH ROW
    EXECUTE FUNCTION calculate_episode_statistics();

-- Function to validate clinical thresholds
CREATE OR REPLACE FUNCTION validate_clinical_thresholds()
RETURNS TRIGGER AS $
BEGIN
    -- Ensure threshold progression: normal < pusher < severe
    IF NEW.normal_threshold >= NEW.pusher_threshold THEN
        RAISE EXCEPTION 'Normal threshold must be less than pusher threshold';
    END IF;
    
    IF NEW.pusher_threshold >= NEW.severe_threshold THEN
        RAISE EXCEPTION 'Pusher threshold must be less than severe threshold';
    END IF;
    
    -- Auto-increment version for new thresholds
    IF TG_OP = 'INSERT' THEN
        SELECT COALESCE(MAX(version), 0) + 1 
        INTO NEW.version
        FROM clinical_thresholds 
        WHERE patient_id = NEW.patient_id;
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Trigger to validate clinical thresholds
CREATE TRIGGER validate_clinical_thresholds_trigger
    BEFORE INSERT OR UPDATE ON clinical_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION validate_clinical_thresholds();

-- Function to update device connection status
CREATE OR REPLACE FUNCTION update_device_connection_status()
RETURNS TRIGGER AS $
BEGIN
    -- Update last_seen timestamp when sensor data is received
    IF TG_OP = 'INSERT' AND NEW.device_id IS NOT NULL THEN
        UPDATE esp32_devices 
        SET 
            last_seen = NOW(),
            last_data_timestamp = NEW.timestamp,
            connection_status = 'connected'
        WHERE device_id = NEW.device_id;
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Trigger to update device status from sensor readings
CREATE TRIGGER update_device_status_from_readings
    AFTER INSERT ON sensor_readings
    FOR EACH ROW
    EXECUTE FUNCTION update_device_connection_status();

-- ============================================================================
-- VIEWS FOR CLINICAL ANALYTICS
-- ============================================================================

-- View for daily episode summary
CREATE OR REPLACE VIEW daily_episode_summary AS
SELECT 
    patient_id,
    device_id,
    DATE(episode_start) as episode_date,
    COUNT(*) as total_episodes,
    AVG(severity_score) as avg_severity,
    MAX(severity_score) as max_severity,
    SUM(episode_duration_seconds) as total_episode_time,
    AVG(max_tilt_angle) as avg_max_tilt,
    MAX(max_tilt_angle) as max_tilt_angle,
    AVG(resistance_index) as avg_resistance,
    SUM(correction_attempts) as total_corrections,
    AVG(correction_success_rate) as avg_correction_success
FROM pusher_episodes
GROUP BY patient_id, device_id, DATE(episode_start);

-- View for active clinical configurations
CREATE OR REPLACE VIEW active_clinical_config AS
SELECT 
    ct.patient_id,
    ct.paretic_side,
    ct.normal_threshold,
    ct.pusher_threshold,
    ct.severe_threshold,
    ct.resistance_threshold,
    ct.non_paretic_threshold,
    ct.created_by as therapist_id,
    ct.version,
    ct.effective_date,
    dc.device_id,
    dc.baseline_pitch,
    dc.baseline_fsr_ratio,
    dc.calibration_date,
    dc.validation_status as calibration_status
FROM clinical_thresholds ct
LEFT JOIN device_calibrations dc ON ct.patient_id = dc.patient_id AND dc.is_active = true
WHERE ct.is_active = true;

-- ============================================================================
-- SAMPLE DATA FOR DEVELOPMENT (commented out for production)
-- ============================================================================

-- Sample clinical thresholds
-- INSERT INTO clinical_thresholds (patient_id, paretic_side, created_by, therapist_notes)
-- SELECT id, 'right', 'therapist_001', 'Initial assessment thresholds'
-- FROM patients 
-- WHERE email = 'test@example.com'
-- LIMIT 1;

-- Sample ESP32 device
-- INSERT INTO esp32_devices (device_id, device_name, firmware_version, connection_status)
-- VALUES ('ESP32_001', 'Vertex Wearable Device #1', '1.0.0', 'disconnected');