-- Migration: Security and Validation Enhancements
-- Date: 2024-01-XX
-- Description: Add comprehensive Row Level Security policies, data validation constraints, and HIPAA compliance measures
-- Task: 8.3 Implement database migration scripts
-- Requirements: 9.3, 9.6 - Authentication, authorization, and HIPAA compliance

-- ============================================================================
-- DATA VALIDATION CONSTRAINTS
-- ============================================================================

-- Enhanced constraints for sensor_readings table
ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_imu_pitch_range 
    CHECK (imu_pitch >= -180.0 AND imu_pitch <= 180.0);

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_imu_roll_range 
    CHECK (imu_roll >= -180.0 AND imu_roll <= 180.0);

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_imu_yaw_range 
    CHECK (imu_yaw >= -180.0 AND imu_yaw <= 180.0);

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_fsr_left_range 
    CHECK (fsr_left >= 0.0 AND fsr_left <= 4095.0);

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_fsr_right_range 
    CHECK (fsr_right >= 0.0 AND fsr_right <= 4095.0);

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_confidence_level_range 
    CHECK (confidence_level IS NULL OR (confidence_level >= 0.0 AND confidence_level <= 1.0));

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_clinical_score_range 
    CHECK (clinical_score IS NULL OR (clinical_score >= 0 AND clinical_score <= 3));

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_weight_ratio_range 
    CHECK (weight_ratio IS NULL OR (weight_ratio >= 0.0 AND weight_ratio <= 1.0));

ALTER TABLE sensor_readings ADD CONSTRAINT IF NOT EXISTS check_data_quality_range 
    CHECK (data_quality IS NULL OR (data_quality >= 0.0 AND data_quality <= 1.0));

-- Enhanced constraints for pusher_episodes table
ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_episode_duration_positive 
    CHECK (episode_duration_seconds > 0.0);

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_episode_start_before_end 
    CHECK (episode_start < episode_end);

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_max_tilt_angle_range 
    CHECK (max_tilt_angle >= -45.0 AND max_tilt_angle <= 45.0);

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_mean_tilt_angle_range 
    CHECK (mean_tilt_angle IS NULL OR (mean_tilt_angle >= -45.0 AND mean_tilt_angle <= 45.0));

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_resistance_index_range 
    CHECK (resistance_index IS NULL OR (resistance_index >= 0.0 AND resistance_index <= 10.0));

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_correction_success_rate_range 
    CHECK (correction_success_rate IS NULL OR (correction_success_rate >= 0.0 AND correction_success_rate <= 1.0));

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_weight_ratios_range 
    CHECK (
        (initial_weight_ratio IS NULL OR (initial_weight_ratio >= 0.0 AND initial_weight_ratio <= 1.0)) AND
        (final_weight_ratio IS NULL OR (final_weight_ratio >= 0.0 AND final_weight_ratio <= 1.0))
    );

ALTER TABLE pusher_episodes ADD CONSTRAINT IF NOT EXISTS check_weight_shift_magnitude_range 
    CHECK (weight_shift_magnitude IS NULL OR (weight_shift_magnitude >= 0.0 AND weight_shift_magnitude <= 1.0));

-- Enhanced constraints for clinical_thresholds table
ALTER TABLE clinical_thresholds ADD CONSTRAINT IF NOT EXISTS check_threshold_progression 
    CHECK (normal_threshold < pusher_threshold AND pusher_threshold < severe_threshold);

ALTER TABLE clinical_thresholds ADD CONSTRAINT IF NOT EXISTS check_stroke_severity_range 
    CHECK (stroke_severity IS NULL OR (stroke_severity >= 1 AND stroke_severity <= 5));

ALTER TABLE clinical_thresholds ADD CONSTRAINT IF NOT EXISTS check_correction_time_window_positive 
    CHECK (correction_time_window > 0.0);

ALTER TABLE clinical_thresholds ADD CONSTRAINT IF NOT EXISTS check_episode_gap_max_positive 
    CHECK (episode_gap_max > 0.0);

ALTER TABLE clinical_thresholds ADD CONSTRAINT IF NOT EXISTS check_effective_before_expiry 
    CHECK (expiry_date IS NULL OR effective_date < expiry_date);

-- Enhanced constraints for esp32_devices table
ALTER TABLE esp32_devices ADD CONSTRAINT IF NOT EXISTS check_battery_level_range 
    CHECK (battery_level IS NULL OR (battery_level >= 0 AND battery_level <= 100));

ALTER TABLE esp32_devices ADD CONSTRAINT IF NOT EXISTS check_signal_strength_range 
    CHECK (signal_strength IS NULL OR (signal_strength >= -100 AND signal_strength <= 0));

ALTER TABLE esp32_devices ADD CONSTRAINT IF NOT EXISTS check_total_uptime_positive 
    CHECK (total_uptime_hours >= 0.0);

ALTER TABLE esp32_devices ADD CONSTRAINT IF NOT EXISTS check_total_sessions_positive 
    CHECK (total_sessions >= 0);

-- Enhanced constraints for device_calibrations table
ALTER TABLE device_calibrations ADD CONSTRAINT IF NOT EXISTS check_calibration_duration_positive 
    CHECK (calibration_duration > 0);

ALTER TABLE device_calibrations ADD CONSTRAINT IF NOT EXISTS check_sample_count_positive 
    CHECK (sample_count IS NULL OR sample_count > 0);

ALTER TABLE device_calibrations ADD CONSTRAINT IF NOT EXISTS check_sample_rate_positive 
    CHECK (sample_rate IS NULL OR sample_rate > 0.0);

ALTER TABLE device_calibrations ADD CONSTRAINT IF NOT EXISTS check_calibration_quality_range 
    CHECK (calibration_quality IS NULL OR (calibration_quality >= 0.0 AND calibration_quality <= 1.0));

ALTER TABLE device_calibrations ADD CONSTRAINT IF NOT EXISTS check_baseline_fsr_ratio_range 
    CHECK (baseline_fsr_ratio IS NULL OR (baseline_fsr_ratio >= 0.0 AND baseline_fsr_ratio <= 1.0));

-- Enhanced constraints for patients table
ALTER TABLE patients ADD CONSTRAINT IF NOT EXISTS check_age_range 
    CHECK (age IS NULL OR (age >= 0 AND age <= 150));

ALTER TABLE patients ADD CONSTRAINT IF NOT EXISTS check_severity_level_range 
    CHECK (severity_level IS NULL OR (severity_level >= 1 AND severity_level <= 5));

ALTER TABLE patients ADD CONSTRAINT IF NOT EXISTS check_stroke_timeline_positive 
    CHECK (stroke_timeline IS NULL OR stroke_timeline >= 0);

-- ============================================================================
-- ENHANCED ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Drop existing policies to recreate with enhanced security
DROP POLICY IF EXISTS "Patients can view own sensor readings" ON sensor_readings;
DROP POLICY IF EXISTS "Patients can insert own sensor readings" ON sensor_readings;
DROP POLICY IF EXISTS "Patients can view own pusher episodes" ON pusher_episodes;
DROP POLICY IF EXISTS "Patients can manage own pusher episodes" ON pusher_episodes;
DROP POLICY IF EXISTS "Therapists can manage patient episodes" ON pusher_episodes;
DROP POLICY IF EXISTS "Patients can view own clinical thresholds" ON clinical_thresholds;
DROP POLICY IF EXISTS "Therapists can manage clinical thresholds" ON clinical_thresholds;
DROP POLICY IF EXISTS "Service can manage ESP32 devices" ON esp32_devices;
DROP POLICY IF EXISTS "Patients can view assigned devices" ON esp32_devices;

-- ============================================================================
-- SENSOR READINGS POLICIES - HIPAA Compliant
-- ============================================================================

-- Patients can only view their own sensor readings
CREATE POLICY "patients_view_own_sensor_readings" ON sensor_readings
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
        OR patient_id IN (
            SELECT id FROM patients 
            WHERE id = auth.uid()::uuid
        )
    );

-- Patients can insert their own sensor readings
CREATE POLICY "patients_insert_own_sensor_readings" ON sensor_readings
    FOR INSERT WITH CHECK (
        patient_id = auth.uid()::uuid
        OR patient_id IN (
            SELECT id FROM patients 
            WHERE id = auth.uid()::uuid
        )
    );

-- Healthcare providers can view sensor readings for their patients
CREATE POLICY "healthcare_providers_view_patient_sensor_readings" ON sensor_readings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = sensor_readings.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
            AND ppr.access_level IN ('read', 'write', 'admin')
        )
    );

-- System services can manage sensor readings (for ESP32 integration)
CREATE POLICY "system_service_manage_sensor_readings" ON sensor_readings
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
    );

-- ============================================================================
-- PUSHER EPISODES POLICIES - Clinical Data Protection
-- ============================================================================

-- Patients can view their own pusher episodes
CREATE POLICY "patients_view_own_pusher_episodes" ON pusher_episodes
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Patients can update their own episode notes (limited fields)
CREATE POLICY "patients_update_own_episode_notes" ON pusher_episodes
    FOR UPDATE USING (
        patient_id = auth.uid()::uuid
    ) WITH CHECK (
        patient_id = auth.uid()::uuid
        -- Only allow updates to specific fields
        AND OLD.severity_score = NEW.severity_score
        AND OLD.max_tilt_angle = NEW.max_tilt_angle
        AND OLD.episode_start = NEW.episode_start
        AND OLD.episode_end = NEW.episode_end
    );

-- Healthcare providers can manage episodes for their patients
CREATE POLICY "healthcare_providers_manage_patient_episodes" ON pusher_episodes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = pusher_episodes.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
            AND ppr.access_level IN ('write', 'admin')
        )
        OR therapist_id = auth.uid()::text
    );

-- Clinical researchers can view anonymized episode data
CREATE POLICY "researchers_view_anonymized_episodes" ON pusher_episodes
    FOR SELECT USING (
        auth.jwt() ->> 'role' = 'researcher'
        AND created_at < NOW() - INTERVAL '30 days' -- Only historical data
    );

-- System services can create episodes from real-time analysis
CREATE POLICY "system_service_create_episodes" ON pusher_episodes
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
    );

-- ============================================================================
-- CLINICAL THRESHOLDS POLICIES - Therapist Authorization Required
-- ============================================================================

-- Patients can view their own clinical thresholds (read-only)
CREATE POLICY "patients_view_own_clinical_thresholds" ON clinical_thresholds
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Only licensed therapists can create/modify clinical thresholds
CREATE POLICY "therapists_manage_clinical_thresholds" ON clinical_thresholds
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'therapist'
        OR auth.jwt() ->> 'role' = 'clinician'
        OR created_by = auth.uid()::text
        OR approved_by = auth.uid()::text
    ) WITH CHECK (
        auth.jwt() ->> 'role' = 'therapist'
        OR auth.jwt() ->> 'role' = 'clinician'
        OR auth.jwt() ->> 'role' = 'admin'
    );

-- Healthcare providers can view thresholds for their patients
CREATE POLICY "healthcare_providers_view_patient_thresholds" ON clinical_thresholds
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = clinical_thresholds.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
        )
    );

-- System services can read thresholds for real-time processing
CREATE POLICY "system_service_read_thresholds" ON clinical_thresholds
    FOR SELECT USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
    );

-- ============================================================================
-- ESP32 DEVICES POLICIES - Device Management Security
-- ============================================================================

-- Patients can view devices assigned to them
CREATE POLICY "patients_view_assigned_devices" ON esp32_devices
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Healthcare providers can manage devices for their patients
CREATE POLICY "healthcare_providers_manage_patient_devices" ON esp32_devices
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = esp32_devices.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
            AND ppr.access_level IN ('write', 'admin')
        )
        OR auth.jwt() ->> 'role' = 'device_admin'
    );

-- System services can manage all devices (for connection tracking)
CREATE POLICY "system_service_manage_all_devices" ON esp32_devices
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
        OR auth.jwt() ->> 'role' = 'device_admin'
    );

-- Device technicians can update device status and maintenance
CREATE POLICY "device_technicians_update_device_status" ON esp32_devices
    FOR UPDATE USING (
        auth.jwt() ->> 'role' = 'device_technician'
        OR auth.jwt() ->> 'role' = 'device_admin'
    ) WITH CHECK (
        -- Only allow updates to specific maintenance fields
        OLD.device_id = NEW.device_id
        AND OLD.patient_id = NEW.patient_id
    );

-- ============================================================================
-- DEVICE CALIBRATIONS POLICIES - Calibration Data Security
-- ============================================================================

-- Patients can view their own device calibrations
CREATE POLICY "patients_view_own_calibrations" ON device_calibrations
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Healthcare providers can manage calibrations for their patients
CREATE POLICY "healthcare_providers_manage_patient_calibrations" ON device_calibrations
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = device_calibrations.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
            AND ppr.access_level IN ('write', 'admin')
        )
        OR validated_by = auth.uid()::text
    );

-- System services can create calibrations from ESP32 data
CREATE POLICY "system_service_manage_calibrations" ON device_calibrations
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
    );

-- ============================================================================
-- MONITORING SESSIONS POLICIES - Session Data Protection
-- ============================================================================

-- Enhanced policies for monitoring_sessions table
DROP POLICY IF EXISTS "Patients can view own sessions" ON monitoring_sessions;
DROP POLICY IF EXISTS "Patients can manage own sessions" ON monitoring_sessions;

-- Patients can view their own monitoring sessions
CREATE POLICY "patients_view_own_monitoring_sessions" ON monitoring_sessions
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Patients can create and update their own sessions
CREATE POLICY "patients_manage_own_monitoring_sessions" ON monitoring_sessions
    FOR ALL USING (
        patient_id = auth.uid()::uuid
    ) WITH CHECK (
        patient_id = auth.uid()::uuid
    );

-- Healthcare providers can view sessions for their patients
CREATE POLICY "healthcare_providers_view_patient_sessions" ON monitoring_sessions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = monitoring_sessions.patient_id
            AND ppr.provider_id = auth.uid()::uuid
            AND ppr.is_active = true
        )
    );

-- System services can manage sessions
CREATE POLICY "system_service_manage_sessions" ON monitoring_sessions
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'service_role'
        OR auth.jwt() ->> 'role' = 'system'
    );

-- ============================================================================
-- PATIENT PROVIDER RELATIONSHIPS TABLE - Healthcare Team Management
-- ============================================================================

-- Create patient-provider relationships table for healthcare team management
CREATE TABLE IF NOT EXISTS patient_provider_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
    provider_id UUID NOT NULL, -- References auth.users(id)
    provider_type VARCHAR CHECK (provider_type IN ('therapist', 'physician', 'nurse', 'researcher', 'admin')) NOT NULL,
    access_level VARCHAR CHECK (access_level IN ('read', 'write', 'admin')) NOT NULL DEFAULT 'read',
    is_active BOOLEAN DEFAULT TRUE,
    relationship_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    relationship_end TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL, -- Who established this relationship
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for patient_provider_relationships
CREATE INDEX IF NOT EXISTS idx_patient_provider_relationships_patient 
    ON patient_provider_relationships(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_patient_provider_relationships_provider 
    ON patient_provider_relationships(provider_id, is_active);

-- RLS for patient_provider_relationships
ALTER TABLE patient_provider_relationships ENABLE ROW LEVEL SECURITY;

-- Patients can view their healthcare team
CREATE POLICY "patients_view_own_healthcare_team" ON patient_provider_relationships
    FOR SELECT USING (
        patient_id = auth.uid()::uuid
    );

-- Healthcare providers can view their patient relationships
CREATE POLICY "providers_view_own_patient_relationships" ON patient_provider_relationships
    FOR SELECT USING (
        provider_id = auth.uid()::uuid
    );

-- Only admins can create/modify provider relationships
CREATE POLICY "admins_manage_provider_relationships" ON patient_provider_relationships
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'admin'
        OR auth.jwt() ->> 'role' = 'healthcare_admin'
        OR created_by = auth.uid()::uuid
    );

-- ============================================================================
-- AUDIT LOGGING - HIPAA Compliance
-- ============================================================================

-- Create audit log table for HIPAA compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR NOT NULL,
    record_id UUID,
    operation VARCHAR CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE', 'SELECT')) NOT NULL,
    user_id UUID,
    user_role VARCHAR,
    ip_address INET,
    user_agent TEXT,
    changed_fields JSONB,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_log_table_timestamp 
    ON audit_log(table_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_timestamp 
    ON audit_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_record 
    ON audit_log(table_name, record_id, timestamp DESC);

-- RLS for audit log (only admins can view)
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admins_view_audit_log" ON audit_log
    FOR SELECT USING (
        auth.jwt() ->> 'role' = 'admin'
        OR auth.jwt() ->> 'role' = 'security_admin'
        OR auth.jwt() ->> 'role' = 'compliance_officer'
    );

-- Function to create audit log entries
CREATE OR REPLACE FUNCTION create_audit_log_entry()
RETURNS TRIGGER AS $
DECLARE
    user_id_val UUID;
    user_role_val VARCHAR;
    changed_fields_val JSONB;
    old_values_val JSONB;
    new_values_val JSONB;
BEGIN
    -- Get user information
    user_id_val := auth.uid();
    user_role_val := auth.jwt() ->> 'role';
    
    -- Determine changed fields and values
    IF TG_OP = 'INSERT' THEN
        new_values_val := to_jsonb(NEW);
        old_values_val := NULL;
        changed_fields_val := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        new_values_val := to_jsonb(NEW);
        old_values_val := to_jsonb(OLD);
        -- Calculate changed fields (simplified)
        changed_fields_val := jsonb_build_object('updated', true);
    ELSIF TG_OP = 'DELETE' THEN
        new_values_val := NULL;
        old_values_val := to_jsonb(OLD);
        changed_fields_val := NULL;
    END IF;
    
    -- Insert audit log entry
    INSERT INTO audit_log (
        table_name, record_id, operation, user_id, user_role,
        changed_fields, old_values, new_values
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        user_id_val,
        user_role_val,
        changed_fields_val,
        old_values_val,
        new_values_val
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit triggers for sensitive tables
CREATE TRIGGER audit_patients_trigger
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW EXECUTE FUNCTION create_audit_log_entry();

CREATE TRIGGER audit_sensor_readings_trigger
    AFTER INSERT OR UPDATE OR DELETE ON sensor_readings
    FOR EACH ROW EXECUTE FUNCTION create_audit_log_entry();

CREATE TRIGGER audit_pusher_episodes_trigger
    AFTER INSERT OR UPDATE OR DELETE ON pusher_episodes
    FOR EACH ROW EXECUTE FUNCTION create_audit_log_entry();

CREATE TRIGGER audit_clinical_thresholds_trigger
    AFTER INSERT OR UPDATE OR DELETE ON clinical_thresholds
    FOR EACH ROW EXECUTE FUNCTION create_audit_log_entry();

-- ============================================================================
-- DATA RETENTION POLICIES - HIPAA Compliance
-- ============================================================================

-- Function to clean up old sensor readings based on retention policy
CREATE OR REPLACE FUNCTION cleanup_old_sensor_readings(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete sensor readings older than retention period
    DELETE FROM sensor_readings 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the cleanup operation
    INSERT INTO audit_log (
        table_name, operation, user_id, user_role, 
        changed_fields, timestamp
    ) VALUES (
        'sensor_readings', 'DELETE', 
        '00000000-0000-0000-0000-000000000000'::uuid, 'system',
        jsonb_build_object('cleanup_count', deleted_count, 'retention_days', retention_days),
        NOW()
    );
    
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to anonymize old patient data for research
CREATE OR REPLACE FUNCTION anonymize_old_patient_data(anonymize_after_days INTEGER DEFAULT 2555) -- ~7 years
RETURNS INTEGER AS $
DECLARE
    anonymized_count INTEGER;
BEGIN
    -- Anonymize patient data older than specified period
    UPDATE patients 
    SET 
        email = 'anonymized_' || id::text || '@example.com',
        full_name = 'Anonymized Patient',
        phone = NULL
    WHERE created_at < NOW() - INTERVAL '1 day' * anonymize_after_days
    AND email NOT LIKE 'anonymized_%';
    
    GET DIAGNOSTICS anonymized_count = ROW_COUNT;
    
    -- Log the anonymization operation
    INSERT INTO audit_log (
        table_name, operation, user_id, user_role,
        changed_fields, timestamp
    ) VALUES (
        'patients', 'UPDATE',
        '00000000-0000-0000-0000-000000000000'::uuid, 'system',
        jsonb_build_object('anonymized_count', anonymized_count, 'anonymize_after_days', anonymize_after_days),
        NOW()
    );
    
    RETURN anonymized_count;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- SECURITY FUNCTIONS - Additional Protection
-- ============================================================================

-- Function to validate user permissions for sensitive operations
CREATE OR REPLACE FUNCTION validate_user_permissions(
    required_role VARCHAR,
    patient_id_param UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $
DECLARE
    user_role VARCHAR;
    has_permission BOOLEAN := FALSE;
BEGIN
    user_role := auth.jwt() ->> 'role';
    
    -- Check direct role match
    IF user_role = required_role THEN
        has_permission := TRUE;
    END IF;
    
    -- Check patient-provider relationship if patient_id provided
    IF patient_id_param IS NOT NULL AND NOT has_permission THEN
        SELECT EXISTS (
            SELECT 1 FROM patient_provider_relationships ppr
            WHERE ppr.patient_id = patient_id_param
            AND ppr.provider_id = auth.uid()
            AND ppr.is_active = true
            AND ppr.access_level IN ('write', 'admin')
        ) INTO has_permission;
    END IF;
    
    -- Check if user is the patient themselves
    IF patient_id_param IS NOT NULL AND NOT has_permission THEN
        has_permission := (auth.uid() = patient_id_param);
    END IF;
    
    RETURN has_permission;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- ROLLBACK SQL (for automated rollback support)
-- ============================================================================

-- ROLLBACK:
-- -- Remove audit triggers
-- DROP TRIGGER IF EXISTS audit_patients_trigger ON patients;
-- DROP TRIGGER IF EXISTS audit_sensor_readings_trigger ON sensor_readings;
-- DROP TRIGGER IF EXISTS audit_pusher_episodes_trigger ON pusher_episodes;
-- DROP TRIGGER IF EXISTS audit_clinical_thresholds_trigger ON clinical_thresholds;
-- 
-- -- Drop audit functions
-- DROP FUNCTION IF EXISTS create_audit_log_entry();
-- DROP FUNCTION IF EXISTS cleanup_old_sensor_readings(INTEGER);
-- DROP FUNCTION IF EXISTS anonymize_old_patient_data(INTEGER);
-- DROP FUNCTION IF EXISTS validate_user_permissions(VARCHAR, UUID);
-- 
-- -- Drop audit and relationship tables
-- DROP TABLE IF EXISTS audit_log;
-- DROP TABLE IF EXISTS patient_provider_relationships;
-- 
-- -- Remove enhanced constraints (keep basic ones)
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_imu_pitch_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_imu_roll_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_imu_yaw_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_fsr_left_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_fsr_right_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_confidence_level_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_clinical_score_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_weight_ratio_range;
-- ALTER TABLE sensor_readings DROP CONSTRAINT IF EXISTS check_data_quality_range;
-- 
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_episode_duration_positive;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_episode_start_before_end;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_max_tilt_angle_range;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_mean_tilt_angle_range;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_resistance_index_range;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_correction_success_rate_range;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_weight_ratios_range;
-- ALTER TABLE pusher_episodes DROP CONSTRAINT IF EXISTS check_weight_shift_magnitude_range;
-- 
-- ALTER TABLE clinical_thresholds DROP CONSTRAINT IF EXISTS check_threshold_progression;
-- ALTER TABLE clinical_thresholds DROP CONSTRAINT IF EXISTS check_stroke_severity_range;
-- ALTER TABLE clinical_thresholds DROP CONSTRAINT IF EXISTS check_correction_time_window_positive;
-- ALTER TABLE clinical_thresholds DROP CONSTRAINT IF EXISTS check_episode_gap_max_positive;
-- ALTER TABLE clinical_thresholds DROP CONSTRAINT IF EXISTS check_effective_before_expiry;
-- 
-- -- Restore original simple policies
-- CREATE POLICY "Patients can view own sensor readings" ON sensor_readings
--     FOR SELECT USING (patient_id IN (SELECT id FROM patients WHERE auth.uid()::text = id::text));
-- CREATE POLICY "Patients can insert own sensor readings" ON sensor_readings
--     FOR INSERT WITH CHECK (patient_id IN (SELECT id FROM patients WHERE auth.uid()::text = id::text));
-- END ROLLBACK