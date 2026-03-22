// Secure Supabase Service with HTTPS Enforcement and Data Cleanup
// Requirements 9.2, 9.3, 9.7: HTTPS encryption, authentication, and data cleanup

import { createClient } from '@supabase/supabase-js';
import { dataCleanupManager } from '../security/dataCleanup';

// Validate HTTPS configuration
const validateHttpsConfig = () => {
  const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
  
  if (!supabaseUrl) {
    throw new Error('REACT_APP_SUPABASE_URL environment variable is required');
  }
  
  if (!supabaseUrl.startsWith('https://')) {
    throw new Error('Supabase URL must use HTTPS protocol for security compliance');
  }
  
  return supabaseUrl;
};

// Secure Supabase configuration with HTTPS enforcement
const supabaseUrl = validateHttpsConfig();
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!supabaseAnonKey) {
  throw new Error('REACT_APP_SUPABASE_ANON_KEY environment variable is required');
}

// Create Supabase client with security options
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Enhanced security options
    persistSession: true,
    detectSessionInUrl: true,
    autoRefreshToken: true,
    
    // Security callbacks for session management
    onAuthStateChange: (event, session) => {
      console.info(`Auth state changed: ${event}`);
      
      if (event === 'SIGNED_OUT' || event === 'TOKEN_REFRESHED') {
        // Clear sensitive data on logout or token refresh
        dataCleanupManager.performCleanup();
      }
      
      if (event === 'SIGNED_IN' && session) {
        // Register session data as sensitive
        dataCleanupManager.registerSensitiveData('supabase.auth.session');
        dataCleanupManager.registerSensitiveData(`user_${session.user.id}`);
      }
    }
  },
  
  // Additional security headers
  global: {
    headers: {
      'User-Agent': 'Vertex-Rehabilitation-Frontend/1.0',
      'X-Client-Info': 'vertex-frontend'
    }
  }
});

// Enhanced authentication service with security measures
export const secureAuthService = {
  // Sign up new patient with data cleanup registration
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
      
      // Register user data as sensitive
      if (data.user) {
        dataCleanupManager.registerSensitiveData(`user_${data.user.id}`);
        dataCleanupManager.registerSensitiveData('patient_profile');
      }
      
      return { success: true, data };
    } catch (error) {
      console.error('Secure sign up error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Sign in existing patient with session security
  async signIn(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) throw error;
      
      // Register session data as sensitive
      if (data.session) {
        dataCleanupManager.registerSensitiveData('supabase.auth.session');
        dataCleanupManager.registerSensitiveData(`user_${data.user.id}`);
        dataCleanupManager.registerSensitiveData('patient_profile');
        
        // Schedule automatic cleanup after session timeout
        dataCleanupManager.scheduleCleanup(30); // 30 minutes
      }
      
      return { success: true, data };
    } catch (error) {
      console.error('Secure sign in error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Secure sign out with immediate data cleanup
  async signOut() {
    try {
      // Perform data cleanup before signing out
      dataCleanupManager.performCleanup();
      
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
      
      // Additional cleanup after sign out
      setTimeout(() => {
        dataCleanupManager.performCleanup();
      }, 1000);
      
      return { success: true };
    } catch (error) {
      console.error('Secure sign out error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Get current session with security validation
  async getSession() {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;
      
      // Validate session security
      if (session) {
        // Check if session is still valid and not expired
        const now = new Date().getTime();
        const expiresAt = new Date(session.expires_at).getTime();
        
        if (now >= expiresAt) {
          console.warn('Session expired, performing cleanup');
          await this.signOut();
          return { success: false, error: 'Session expired' };
        }
        
        // Register session as sensitive data
        dataCleanupManager.registerSensitiveData('supabase.auth.session');
      }
      
      return { success: true, session };
    } catch (error) {
      console.error('Get session error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Refresh token with security measures
  async refreshToken() {
    try {
      const { data, error } = await supabase.auth.refreshSession();
      if (error) throw error;
      
      // Clean old session data and register new
      dataCleanupManager.performCleanup();
      
      if (data.session) {
        dataCleanupManager.registerSensitiveData('supabase.auth.session');
        dataCleanupManager.registerSensitiveData(`user_${data.user.id}`);
      }
      
      return { success: true, data };
    } catch (error) {
      console.error('Token refresh error:', error.message);
      return { success: false, error: error.message };
    }
  }
};

// Secure patient service with data protection
export const securePatientService = {
  // Create patient profile with data cleanup registration
  async createProfile(patientData) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .insert([patientData])
        .select()
        .single();
      
      if (error) throw error;
      
      // Register patient data as sensitive
      dataCleanupManager.registerSensitiveData(`patient_${data.id}`);
      dataCleanupManager.registerSensitiveData('patient_profile');
      
      return { success: true, data };
    } catch (error) {
      console.error('Create profile error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Get patient profile with security validation
  async getProfile(patientId) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .select('*')
        .eq('id', patientId)
        .single();
      
      if (error) throw error;
      
      // Register retrieved data as sensitive
      dataCleanupManager.registerSensitiveData(`patient_${patientId}`);
      dataCleanupManager.registerSensitiveData('patient_profile');
      
      return { success: true, data };
    } catch (error) {
      console.error('Get profile error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Update patient profile with security measures
  async updateProfile(patientId, updates) {
    try {
      const { data, error } = await supabase
        .from('patients')
        .update(updates)
        .eq('id', patientId)
        .select()
        .single();
      
      if (error) throw error;
      
      // Clean old data and register updated data
      dataCleanupManager.registerSensitiveData(`patient_${patientId}`);
      dataCleanupManager.registerSensitiveData('patient_profile');
      
      return { success: true, data };
    } catch (error) {
      console.error('Update profile error:', error.message);
      return { success: false, error: error.message };
    }
  }
};

// Secure device calibration service
export const secureCalibrationService = {
  // Save calibration settings with data protection
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
      
      // Register calibration data as sensitive
      dataCleanupManager.registerSensitiveData(`calibration_${patientId}`);
      dataCleanupManager.registerSensitiveData('device_calibration');
      
      return { success: true, data };
    } catch (error) {
      console.error('Save calibration error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Get active calibration with security measures
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
      
      // Register calibration data as sensitive
      dataCleanupManager.registerSensitiveData(`calibration_${patientId}`);
      dataCleanupManager.registerSensitiveData('device_calibration');
      
      return { success: true, data };
    } catch (error) {
      console.error('Get calibration error:', error.message);
      return { success: false, error: error.message };
    }
  }
};

// Secure sensor data service with minimal data retention
export const secureSensorService = {
  // Save sensor reading with automatic cleanup
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
      
      // Register sensor data as sensitive (with automatic cleanup)
      dataCleanupManager.registerSensitiveData(`sensor_${patientId}`, () => {
        // Custom cleanup for sensor data
        localStorage.removeItem(`sensor_cache_${patientId}`);
        sessionStorage.removeItem(`live_sensor_${patientId}`);
      });
      
      return { success: true, data };
    } catch (error) {
      console.error('Save sensor reading error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Get recent sensor readings with data protection
  async getRecentReadings(patientId, limit = 100) {
    try {
      const { data, error } = await supabase
        .from('sensor_readings')
        .select('*')
        .eq('patient_id', patientId)
        .order('timestamp', { ascending: false })
        .limit(limit);
      
      if (error) throw error;
      
      // Register sensor data as sensitive
      dataCleanupManager.registerSensitiveData(`sensor_${patientId}`);
      
      return { success: true, data };
    } catch (error) {
      console.error('Get recent readings error:', error.message);
      return { success: false, error: error.message };
    }
  }
};

// Secure session management service
export const secureSessionService = {
  // Start monitoring session with security measures
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
      
      // Register session data as sensitive
      dataCleanupManager.registerSensitiveData(`session_${data.id}`);
      dataCleanupManager.registerSensitiveData('monitoring_session');
      
      return { success: true, data };
    } catch (error) {
      console.error('Start session error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // End monitoring session with data cleanup
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
      
      // Clean up session-specific data
      dataCleanupManager.registerSensitiveData(`session_${sessionId}`, () => {
        localStorage.removeItem(`session_cache_${sessionId}`);
        sessionStorage.removeItem(`live_session_${sessionId}`);
      });
      
      return { success: true, data };
    } catch (error) {
      console.error('End session error:', error.message);
      return { success: false, error: error.message };
    }
  },

  // Get session history with data protection
  async getSessionHistory(patientId, limit = 50) {
    try {
      const { data, error } = await supabase
        .from('monitoring_sessions')
        .select('*')
        .eq('patient_id', patientId)
        .order('start_time', { ascending: false })
        .limit(limit);
      
      if (error) throw error;
      
      // Register session history as sensitive
      dataCleanupManager.registerSensitiveData(`sessions_${patientId}`);
      
      return { success: true, data };
    } catch (error) {
      console.error('Get session history error:', error.message);
      return { success: false, error: error.message };
    }
  }
};

// Security utilities
export const securityUtils = {
  // Validate HTTPS connection
  validateSecureConnection() {
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      console.warn('Insecure connection detected. HTTPS required for production.');
      return false;
    }
    return true;
  },

  // Check if data should be encrypted in transit
  requiresEncryption(dataType) {
    const sensitiveDataTypes = [
      'patient_profile',
      'sensor_data',
      'session_data',
      'calibration_data',
      'auth_token'
    ];
    return sensitiveDataTypes.includes(dataType);
  },

  // Generate secure headers for API requests
  getSecureHeaders(includeAuth = true) {
    const headers = {
      'Content-Type': 'application/json',
      'X-Client-Info': 'vertex-frontend',
      'X-Requested-With': 'XMLHttpRequest'
    };

    if (includeAuth) {
      const session = supabase.auth.getSession();
      if (session?.data?.session?.access_token) {
        headers['Authorization'] = `Bearer ${session.data.session.access_token}`;
      }
    }

    return headers;
  }
};

// Export the secure supabase client as default
export default supabase;