-- Migration: Add clinical thresholds management tables
-- Date: 2024-01-XX
-- Description: Add tables for patient-specific clinical thresholds with version history and therapist authorization

-- Clinical thresholds table for patient-specific parameters
CREATE TABLE IF NOT EXISTS clinical_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    paretic_side VARCHAR CHECK (paretic_side IN ('left', 'right')) NOT NULL,
    normal_threshold FLOAT DEFAULT 5.0 CHECK (normal_threshold >= 0.0 AND normal_threshold <= 15.0),
    pusher_threshold FLOAT DEFAULT 10.0 CHECK (pusher_threshold >= 5.0 AND pusher_threshold <= 25.0),
    severe_threshold FLOAT DEFAULT 20.0 CHECK (severe_threshold >= 15.0 AND severe_threshold <= 45.0),
    resistance_threshold FLOAT DEFAULT 2.0 CHECK (resistance_threshold >= 0.5 AND resistance_threshold <= 5.0),
    episode_duration_min FLOAT DEFAULT 2.0 CHECK (episode_duration_min >= 1.0 AND episode_duration_min <= 10.0),
    non_paretic_threshold FLOAT DEFAULT 0.7 CHECK (non_paretic_threshold >= 0.5 AND non_paretic_threshold <= 0.9),
    created_by VARCHAR, -- Therapist ID or username
    therapist_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Threshold history table for version tracking
CREATE TABLE IF NOT EXISTS clinical_threshold_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    threshold_id UUID REFERENCES clinical_thresholds(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    paretic_side VARCHAR NOT NULL,
    normal_threshold FLOAT NOT NULL,
    pusher_threshold FLOAT NOT NULL,
    severe_threshold FLOAT NOT NULL,
    resistance_threshold FLOAT NOT NULL,
    episode_duration_min FLOAT NOT NULL,
    non_paretic_threshold FLOAT NOT NULL,
    created_by VARCHAR,
    therapist_notes TEXT,
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ESP32 device registry and connection tracking (if not exists)
CREATE TABLE IF NOT EXISTS esp32_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR UNIQUE NOT NULL,
    device_name VARCHAR,
    firmware_version VARCHAR,
    last_seen TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    connection_status VARCHAR DEFAULT 'disconnected',
    patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced device calibrations with FSR baselines (extend existing table)
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS device_id VARCHAR;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_left FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_right FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS baseline_fsr_ratio FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS pitch_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS fsr_std_dev FLOAT;
ALTER TABLE device_calibrations ADD COLUMN IF NOT EXISTS calibration_duration INTEGER DEFAULT 30;

-- Enhanced sensor readings with clinical data (extend existing table)
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS pusher_detected BOOLEAN DEFAULT FALSE;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS confidence_level FLOAT;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS clinical_score INTEGER;
ALTER TABLE sensor_readings ADD COLUMN IF NOT EXISTS episode_id UUID;

-- Pusher syndrome episodes with clinical scoring
CREATE TABLE IF NOT EXISTS pusher_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    session_id UUID REFERENCES monitoring_sessions(id) ON DELETE CASCADE,
    episode_start TIMESTAMP WITH TIME ZONE NOT NULL,
    episode_end TIMESTAMP WITH TIME ZONE NOT NULL,
    severity_score INTEGER CHECK (severity_score >= 0 AND severity_score <= 3),
    max_tilt_angle FLOAT NOT NULL,
    resistance_index FLOAT, -- Calculated resistance to correction
    correction_attempts INTEGER DEFAULT 0,
    clinical_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add foreign key for episode tracking in sensor readings
ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS fk_sensor_readings_episode 
    FOREIGN KEY (episode_id) REFERENCES pusher_episodes(id) ON DELETE SET NULL;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_clinical_thresholds_patient_active ON clinical_thresholds(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_clinical_threshold_history_patient ON clinical_threshold_history(patient_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_pusher_episodes_patient_date ON pusher_episodes(patient_id, episode_start DESC);
CREATE INDEX IF NOT EXISTS idx_esp32_devices_status ON esp32_devices(connection_status, last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_episode ON sensor_readings(episode_id, timestamp DESC);

-- Row Level Security policies for clinical thresholds
ALTER TABLE clinical_thresholds ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinical_threshold_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE pusher_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE esp32_devices ENABLE ROW LEVEL SECURITY;

-- Clinical thresholds policies
CREATE POLICY "Patients can view own clinical thresholds" ON clinical_thresholds
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Therapists can manage clinical thresholds" ON clinical_thresholds
    FOR ALL USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
        OR created_by = auth.uid()::text
    );

-- Threshold history policies
CREATE POLICY "Patients can view threshold history" ON clinical_threshold_history
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- Pusher episodes policies
CREATE POLICY "Patients can view own episodes" ON pusher_episodes
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Patients can manage own episodes" ON pusher_episodes
    FOR ALL USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- ESP32 devices policies (allow service access)
CREATE POLICY "Service can manage ESP32 devices" ON esp32_devices
    FOR ALL USING (true);

-- Function to create threshold history entry
CREATE OR REPLACE FUNCTION create_threshold_history()
RETURNS TRIGGER AS $
BEGIN
    -- Insert into history table when threshold is updated
    IF TG_OP = 'UPDATE' AND OLD.is_active = TRUE AND NEW.is_active = FALSE THEN
        INSERT INTO clinical_threshold_history (
            threshold_id, patient_id, version, paretic_side,
            normal_threshold, pusher_threshold, severe_threshold,
            resistance_threshold, episode_duration_min, non_paretic_threshold,
            created_by, therapist_notes, change_reason, created_at
        ) VALUES (
            OLD.id, OLD.patient_id, OLD.version, OLD.paretic_side,
            OLD.normal_threshold, OLD.pusher_threshold, OLD.severe_threshold,
            OLD.resistance_threshold, OLD.episode_duration_min, OLD.non_paretic_threshold,
            OLD.created_by, OLD.therapist_notes, 'Replaced by new version', OLD.created_at
        );
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Trigger to automatically create history entries
CREATE TRIGGER clinical_thresholds_history_trigger
    AFTER UPDATE ON clinical_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION create_threshold_history();

-- Function to automatically update version numbers
CREATE OR REPLACE FUNCTION increment_threshold_version()
RETURNS TRIGGER AS $
BEGIN
    -- Get the next version number for this patient
    SELECT COALESCE(MAX(version), 0) + 1 
    INTO NEW.version
    FROM clinical_thresholds 
    WHERE patient_id = NEW.patient_id;
    
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Trigger to automatically increment version numbers
CREATE TRIGGER clinical_thresholds_version_trigger
    BEFORE INSERT ON clinical_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION increment_threshold_version();