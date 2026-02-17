-- Vertex Mobile Rehabilitation App Database Schema
-- Supabase PostgreSQL Database Setup

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patient profiles and authentication
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    phone VARCHAR,
    age INTEGER,
    stroke_side VARCHAR CHECK (stroke_side IN ('left', 'right', 'both', 'not_sure')),
    severity_level INTEGER CHECK (severity_level >= 1 AND severity_level <= 5),
    mobility_level VARCHAR CHECK (mobility_level IN ('wheelchair', 'walker', 'cane', 'independent')),
    stroke_timeline INTEGER, -- months since stroke
    therapy_status VARCHAR CHECK (therapy_status IN ('active', 'inactive')),
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device sensor readings
CREATE TABLE sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    device_id VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    imu_pitch FLOAT,
    imu_roll FLOAT,
    imu_yaw FLOAT,
    fsr_left FLOAT,
    fsr_right FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Monitoring sessions
CREATE TABLE monitoring_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    upright_percentage FLOAT,
    average_tilt FLOAT,
    correction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device calibration settings
CREATE TABLE device_calibrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    calibration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    baseline_pitch FLOAT,
    baseline_roll FLOAT,
    warning_threshold FLOAT,
    danger_threshold FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_sensor_readings_patient_timestamp ON sensor_readings(patient_id, timestamp DESC);
CREATE INDEX idx_monitoring_sessions_patient ON monitoring_sessions(patient_id, start_time DESC);
CREATE INDEX idx_device_calibrations_patient_active ON device_calibrations(patient_id, is_active);

-- Row Level Security (RLS) policies
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_calibrations ENABLE ROW LEVEL SECURITY;

-- Patients can only access their own data
CREATE POLICY "Patients can view own profile" ON patients
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Patients can update own profile" ON patients
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Sensor readings policies
CREATE POLICY "Patients can view own sensor readings" ON sensor_readings
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Patients can insert own sensor readings" ON sensor_readings
    FOR INSERT WITH CHECK (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- Monitoring sessions policies
CREATE POLICY "Patients can view own sessions" ON monitoring_sessions
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Patients can manage own sessions" ON monitoring_sessions
    FOR ALL USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- Device calibrations policies
CREATE POLICY "Patients can view own calibrations" ON device_calibrations
    FOR SELECT USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

CREATE POLICY "Patients can manage own calibrations" ON device_calibrations
    FOR ALL USING (
        patient_id IN (
            SELECT id FROM patients WHERE auth.uid()::text = id::text
        )
    );

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on patients table
CREATE TRIGGER update_patients_updated_at 
    BEFORE UPDATE ON patients 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to create patient profile after auth signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.patients (id, email, full_name, phone, age, notifications_enabled)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'phone', ''),
        COALESCE((NEW.raw_user_meta_data->>'age')::integer, NULL),
        COALESCE((NEW.raw_user_meta_data->>'notifications_enabled')::boolean, true)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create patient profile on auth signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Sample data for development (optional)
-- INSERT INTO patients (id, email, full_name, age, stroke_side, severity_level, mobility_level, stroke_timeline, therapy_status)
-- VALUES (
--     gen_random_uuid(),
--     'test@example.com',
--     'Test Patient',
--     65,
--     'right',
--     3,
--     'walker',
--     6,
--     'active'
-- );