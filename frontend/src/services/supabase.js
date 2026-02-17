import { createClient } from '@supabase/supabase-js';

// Supabase configuration
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://your-project.supabase.co';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'your-anon-key';

// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Authentication service
export const authService = {
  // Sign up new patient
  async signUp(email, password, userData) {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: userData.fullName,
            phone: userData.phone,
            age: userData.age,
            notifications_enabled: userData.notificationsEnabled
          }
        }
      });
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Sign in existing patient
  async signIn(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Sign out
  async signOut() {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get current session
  async getSession() {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;
      return { success: true, session };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Removed onAuthStateChange to prevent signal abort errors
};

// Patient profile service
export const patientService = {
  // Create patient profile
  async createProfile(patientData) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .insert([patientData])
        .select()
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get patient profile
  async getProfile(patientId) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .select('*')
        .eq('id', patientId)
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Update patient profile
  async updateProfile(patientId, updates) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .update(updates)
        .eq('id', patientId)
        .select()
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Device calibration service
export const calibrationService = {
  // Save calibration settings
  async saveCalibration(patientId, calibrationData) {
    try {
      const { data, error } = await supabase
        .from('device_calibrations')
        .insert([{
          patient_id: patientId,
          calibration_date: new Date().toISOString(),
          baseline_pitch: calibrationData.baselinePitch,
          baseline_roll: calibrationData.baselineRoll,
          warning_threshold: calibrationData.warningThreshold,
          danger_threshold: calibrationData.dangerThreshold,
          is_active: true
        }])
        .select()
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get active calibration
  async getActiveCalibration(patientId) {
    try {
      const { data, error } = await supabase
        .from('device_calibrations')
        .select('*')
        .eq('patient_id', patientId)
        .eq('is_active', true)
        .order('calibration_date', { ascending: false })
        .limit(1)
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Sensor data service
export const sensorService = {
  // Save sensor reading
  async saveSensorReading(patientId, sensorData) {
    try {
      const { data, error } = await supabase
        .from('sensor_readings')
        .insert([{
          patient_id: patientId,
          device_id: sensorData.deviceId,
          timestamp: sensorData.timestamp,
          imu_pitch: sensorData.imuPitch,
          imu_roll: sensorData.imuRoll,
          imu_yaw: sensorData.imuYaw,
          fsr_left: sensorData.fsrLeft,
          fsr_right: sensorData.fsrRight
        }]);
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get recent sensor readings
  async getRecentReadings(patientId, limit = 100) {
    try {
      const { data, error } = await supabase
        .from('sensor_readings')
        .select('*')
        .eq('patient_id', patientId)
        .order('timestamp', { ascending: false })
        .limit(limit);
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

// Session management service
export const sessionService = {
  // Start monitoring session
  async startSession(patientId) {
    try {
      const { data, error } = await supabase
        .from('monitoring_sessions')
        .insert([{
          patient_id: patientId,
          start_time: new Date().toISOString()
        }])
        .select()
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // End monitoring session
  async endSession(sessionId, sessionData) {
    try {
      const { data, error } = await supabase
        .from('monitoring_sessions')
        .update({
          end_time: new Date().toISOString(),
          duration_minutes: sessionData.durationMinutes,
          upright_percentage: sessionData.uprightPercentage,
          average_tilt: sessionData.averageTilt,
          correction_count: sessionData.correctionCount
        })
        .eq('id', sessionId)
        .select()
        .single();
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get session history
  async getSessionHistory(patientId, limit = 50) {
    try {
      const { data, error } = await supabase
        .from('monitoring_sessions')
        .select('*')
        .eq('patient_id', patientId)
        .order('start_time', { ascending: false })
        .limit(limit);
      
      if (error) throw error;
      return { success: true, data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
};

export default supabase;