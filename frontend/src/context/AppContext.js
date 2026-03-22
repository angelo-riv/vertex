import React, { createContext, useContext, useReducer } from 'react';

/**
 * Enhanced AppContext for ESP32 Data Integration
 * 
 * This context manages state for the Vertex Rehabilitation System with ESP32 integration,
 * including real-time sensor data, clinical analytics, and calibration management.
 * 
 * Key Features:
 * - ESP32 device connection and status tracking
 * - Real-time posture monitoring with clinical thresholds
 * - Pusher syndrome detection and episode tracking
 * - Patient-specific calibration and baseline management
 * - Clinical analytics with BLS/4PPS compatible scoring
 */

// Initial state for the Vertex application
const initialState = {
  // Authentication - user should be null when not authenticated
  user: null, // Will contain user data when authenticated
  loading: false, // Set to false initially so we don't get stuck
  
  // Onboarding State
  onboardingComplete: false,
  
  // Device Connection
  device: {
    isConnected: false,
    deviceId: null,
    lastReading: null,
    calibrationStatus: 'not_calibrated' // 'not_calibrated', 'calibrating', 'calibrated'
  },
  
  // Demo Mode
  demo: {
    isActive: false,
    deviceId: null,
    startTime: null,
    currentScenario: 'normal_posture',
    availableScenarios: [],
    duration: 0
  },
  
  // Real-time Monitoring
  monitoring: {
    isActive: false,
    currentSession: null,
    livePosture: {
      timestamp: null,
      tiltAngle: 0,
      tiltDirection: 'center',
      fsrLeft: 0,
      fsrRight: 0,
      balance: 0,
      alertLevel: 'safe', // 'safe', 'warning', 'unsafe'
      hapticActive: false,
      confidenceLevel: 0.0, // 0.0-1.0 confidence in sensor readings
      resistanceIndex: 0.0 // Calculated resistance to correction
    },
    alertLevel: 'safe'
  },
  
  // ESP32 Integration - Real-time device connection and communication
  esp32: {
    isConnected: false,
    deviceId: null,
    lastDataTimestamp: null,
    connectionQuality: 'unknown', // 'excellent', 'good', 'poor', 'disconnected'
    demoMode: false
  },
  
  // Clinical Analytics - Pusher syndrome detection and medical assessment
  clinical: {
    pusherDetected: false,
    currentEpisode: null,
    episodeHistory: [],
    clinicalScore: 0, // BLS/4PPS compatible score
    thresholds: {
      normal: 5.0,
      pusher: 10.0,
      severe: 20.0,
      pareticSide: 'right'
    },
    resistanceIndex: 0.0, // Current resistance to correction
    correctionAttempts: 0, // Number of correction attempts in current episode
    confidenceLevel: 0.0 // Overall confidence in clinical detection
  },
  
  // Calibration State - Patient-specific baseline establishment
  calibration: {
    status: 'not_calibrated', // 'not_calibrated', 'calibrating', 'calibrated'
    progress: 0, // 0-100 for 30-second calibration
    baseline: null, // Will contain { pitch, fsrLeft, fsrRight, ratio, stdDev }
    lastCalibrationDate: null,
    deviceId: null, // Device used for calibration
    calibrationDuration: 30, // seconds
    isActive: false // Whether this calibration is currently active
  },

  // UI State
  ui: {
    currentPage: 'login',
    isLoading: false,
    errors: [],
    notifications: [],
    theme: 'light',
    // ESP32 Alert Management
    esp32Alerts: {
      connectionAlerts: true,
      pusherAlerts: true,
      calibrationReminders: true,
      thresholdAlerts: true,
      alertVolume: 'medium' // 'low', 'medium', 'high', 'muted'
    }
  },
  
  // Onboarding State Details
  onboarding: {
    currentStep: 1,
    totalSteps: 5,
    assessmentData: {
      strokeSide: null,
      severityLevel: null,
      mobilityLevel: null,
      strokeTimeline: null,
      therapyStatus: null
    },
    isComplete: false
  }
};

// Action types
export const ActionTypes = {
  // Authentication actions
  SET_USER: 'SET_USER',
  SET_LOADING: 'SET_LOADING',
  LOGOUT: 'LOGOUT',
  
  // Device actions
  SET_DEVICE_CONNECTION: 'SET_DEVICE_CONNECTION',
  UPDATE_DEVICE_STATUS: 'UPDATE_DEVICE_STATUS',
  SET_CALIBRATION_STATUS: 'SET_CALIBRATION_STATUS',
  
  // Demo mode actions
  START_DEMO_MODE: 'START_DEMO_MODE',
  STOP_DEMO_MODE: 'STOP_DEMO_MODE',
  UPDATE_DEMO_STATUS: 'UPDATE_DEMO_STATUS',
  SET_DEMO_SCENARIO: 'SET_DEMO_SCENARIO',
  
  // ESP32 Integration actions
  SET_ESP32_CONNECTION: 'SET_ESP32_CONNECTION',
  UPDATE_ESP32_STATUS: 'UPDATE_ESP32_STATUS',
  SET_ESP32_DEMO_MODE: 'SET_ESP32_DEMO_MODE',
  
  // Clinical Analytics actions
  SET_PUSHER_DETECTED: 'SET_PUSHER_DETECTED',
  UPDATE_CLINICAL_SCORE: 'UPDATE_CLINICAL_SCORE',
  SET_CLINICAL_THRESHOLDS: 'SET_CLINICAL_THRESHOLDS',
  ADD_EPISODE: 'ADD_EPISODE',
  UPDATE_RESISTANCE_INDEX: 'UPDATE_RESISTANCE_INDEX',
  UPDATE_CORRECTION_ATTEMPTS: 'UPDATE_CORRECTION_ATTEMPTS',
  UPDATE_CLINICAL_CONFIDENCE: 'UPDATE_CLINICAL_CONFIDENCE',
  
  // Calibration actions
  SET_CALIBRATION_STATUS: 'SET_CALIBRATION_STATUS',
  UPDATE_CALIBRATION_PROGRESS: 'UPDATE_CALIBRATION_PROGRESS',
  SET_CALIBRATION_BASELINE: 'SET_CALIBRATION_BASELINE',
  SET_CALIBRATION_DEVICE: 'SET_CALIBRATION_DEVICE',
  SET_CALIBRATION_ACTIVE: 'SET_CALIBRATION_ACTIVE',
  
  // Monitoring actions
  START_MONITORING: 'START_MONITORING',
  STOP_MONITORING: 'STOP_MONITORING',
  UPDATE_LIVE_POSTURE: 'UPDATE_LIVE_POSTURE',
  SET_ALERT_LEVEL: 'SET_ALERT_LEVEL',
  
  // UI actions
  SET_CURRENT_PAGE: 'SET_CURRENT_PAGE',
  SET_UI_LOADING: 'SET_UI_LOADING',
  ADD_ERROR: 'ADD_ERROR',
  REMOVE_ERROR: 'REMOVE_ERROR',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  
  // ESP32 Alert Management actions
  SET_ESP32_ALERT_PREFERENCES: 'SET_ESP32_ALERT_PREFERENCES',
  TOGGLE_ESP32_ALERT_TYPE: 'TOGGLE_ESP32_ALERT_TYPE',
  SET_ALERT_VOLUME: 'SET_ALERT_VOLUME',
  
  // Onboarding actions
  SET_ONBOARDING_STEP: 'SET_ONBOARDING_STEP',
  UPDATE_ASSESSMENT_DATA: 'UPDATE_ASSESSMENT_DATA',
  COMPLETE_ONBOARDING: 'COMPLETE_ONBOARDING',
  RESET_ONBOARDING: 'RESET_ONBOARDING'
};

// Reducer function
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_USER:
      return {
        ...state,
        user: action.payload, // Store user data directly
        loading: false
      };
      
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };
      
    case ActionTypes.LOGOUT:
      return {
        ...state,
        user: null, // Clear user data
        onboardingComplete: false,
        loading: false,
        monitoring: {
          ...initialState.monitoring
        }
      };
      
    case ActionTypes.SET_DEVICE_CONNECTION:
      return {
        ...state,
        device: {
          ...state.device,
          isConnected: action.payload.isConnected,
          deviceId: action.payload.deviceId,
          lastReading: action.payload.isConnected ? new Date() : state.device.lastReading
        }
      };
      
    case ActionTypes.UPDATE_DEVICE_STATUS:
      return {
        ...state,
        device: {
          ...state.device,
          ...action.payload
        }
      };
      
    case ActionTypes.SET_CALIBRATION_STATUS:
      return {
        ...state,
        device: {
          ...state.device,
          calibrationStatus: action.payload
        }
      };
      
    case ActionTypes.START_DEMO_MODE:
      return {
        ...state,
        demo: {
          ...state.demo,
          isActive: true,
          deviceId: action.payload.deviceId,
          startTime: new Date(),
          currentScenario: action.payload.scenario || 'normal_posture'
        }
      };
      
    case ActionTypes.STOP_DEMO_MODE:
      return {
        ...state,
        demo: {
          ...state.demo,
          isActive: false,
          deviceId: null,
          startTime: null,
          duration: 0
        }
      };
      
    case ActionTypes.UPDATE_DEMO_STATUS:
      return {
        ...state,
        demo: {
          ...state.demo,
          ...action.payload
        }
      };
      
    case ActionTypes.SET_DEMO_SCENARIO:
      return {
        ...state,
        demo: {
          ...state.demo,
          currentScenario: action.payload
        }
      };
      
    case ActionTypes.SET_ESP32_CONNECTION:
      return {
        ...state,
        esp32: {
          ...state.esp32,
          isConnected: action.payload.isConnected,
          deviceId: action.payload.deviceId,
          lastDataTimestamp: action.payload.isConnected ? new Date() : state.esp32.lastDataTimestamp,
          connectionQuality: action.payload.isConnected ? 'good' : 'disconnected'
        }
      };
      
    case ActionTypes.UPDATE_ESP32_STATUS:
      return {
        ...state,
        esp32: {
          ...state.esp32,
          ...action.payload
        }
      };
      
    case ActionTypes.SET_ESP32_DEMO_MODE:
      return {
        ...state,
        esp32: {
          ...state.esp32,
          demoMode: action.payload
        }
      };
      
    case ActionTypes.SET_PUSHER_DETECTED:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          pusherDetected: action.payload.detected,
          clinicalScore: action.payload.score || state.clinical.clinicalScore
        }
      };
      
    case ActionTypes.UPDATE_CLINICAL_SCORE:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          clinicalScore: action.payload
        }
      };
      
    case ActionTypes.SET_CLINICAL_THRESHOLDS:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          thresholds: {
            ...state.clinical.thresholds,
            ...action.payload
          }
        }
      };
      
    case ActionTypes.ADD_EPISODE:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          episodeHistory: [action.payload, ...state.clinical.episodeHistory.slice(0, 49)], // Keep last 50 episodes
          currentEpisode: action.payload.isActive ? action.payload : null
        }
      };
      
    case ActionTypes.UPDATE_RESISTANCE_INDEX:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          resistanceIndex: action.payload
        },
        monitoring: {
          ...state.monitoring,
          livePosture: {
            ...state.monitoring.livePosture,
            resistanceIndex: action.payload
          }
        }
      };
      
    case ActionTypes.UPDATE_CORRECTION_ATTEMPTS:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          correctionAttempts: action.payload
        }
      };
      
    case ActionTypes.UPDATE_CLINICAL_CONFIDENCE:
      return {
        ...state,
        clinical: {
          ...state.clinical,
          confidenceLevel: action.payload
        },
        monitoring: {
          ...state.monitoring,
          livePosture: {
            ...state.monitoring.livePosture,
            confidenceLevel: action.payload
          }
        }
      };
      
    case ActionTypes.UPDATE_CALIBRATION_PROGRESS:
      return {
        ...state,
        calibration: {
          ...state.calibration,
          progress: action.payload
        }
      };
      
    case ActionTypes.SET_CALIBRATION_BASELINE:
      return {
        ...state,
        calibration: {
          ...state.calibration,
          baseline: action.payload,
          status: 'calibrated',
          lastCalibrationDate: new Date(),
          isActive: true
        }
      };
      
    case ActionTypes.SET_CALIBRATION_DEVICE:
      return {
        ...state,
        calibration: {
          ...state.calibration,
          deviceId: action.payload
        }
      };
      
    case ActionTypes.SET_CALIBRATION_ACTIVE:
      return {
        ...state,
        calibration: {
          ...state.calibration,
          isActive: action.payload
        }
      };
      
    case ActionTypes.START_MONITORING:
      return {
        ...state,
        monitoring: {
          ...state.monitoring,
          isActive: true,
          currentSession: {
            id: action.payload.sessionId,
            startTime: new Date(),
            duration: 0
          }
        }
      };
      
    case ActionTypes.STOP_MONITORING:
      return {
        ...state,
        monitoring: {
          ...state.monitoring,
          isActive: false,
          currentSession: null
        }
      };
      
    case ActionTypes.UPDATE_LIVE_POSTURE:
      return {
        ...state,
        monitoring: {
          ...state.monitoring,
          livePosture: {
            ...state.monitoring.livePosture,
            ...action.payload,
            timestamp: new Date()
          }
        }
      };
      
    case ActionTypes.SET_ALERT_LEVEL:
      return {
        ...state,
        monitoring: {
          ...state.monitoring,
          alertLevel: action.payload
        }
      };
      
    case ActionTypes.SET_CURRENT_PAGE:
      return {
        ...state,
        ui: {
          ...state.ui,
          currentPage: action.payload
        }
      };
      
    case ActionTypes.SET_UI_LOADING:
      return {
        ...state,
        ui: {
          ...state.ui,
          isLoading: action.payload
        }
      };
      
    case ActionTypes.ADD_ERROR:
      return {
        ...state,
        ui: {
          ...state.ui,
          errors: [...state.ui.errors, {
            id: Date.now(),
            message: action.payload.message,
            type: action.payload.type || 'error',
            timestamp: new Date()
          }]
        }
      };
      
    case ActionTypes.REMOVE_ERROR:
      return {
        ...state,
        ui: {
          ...state.ui,
          errors: state.ui.errors.filter(error => error.id !== action.payload)
        }
      };
      
    case ActionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: [...state.ui.notifications, {
            id: Date.now(),
            message: action.payload.message,
            type: action.payload.type || 'info',
            timestamp: new Date()
          }]
        }
      };
      
    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(notification => notification.id !== action.payload)
        }
      };
      
    case ActionTypes.SET_ESP32_ALERT_PREFERENCES:
      return {
        ...state,
        ui: {
          ...state.ui,
          esp32Alerts: {
            ...state.ui.esp32Alerts,
            ...action.payload
          }
        }
      };
      
    case ActionTypes.TOGGLE_ESP32_ALERT_TYPE:
      return {
        ...state,
        ui: {
          ...state.ui,
          esp32Alerts: {
            ...state.ui.esp32Alerts,
            [action.payload]: !state.ui.esp32Alerts[action.payload]
          }
        }
      };
      
    case ActionTypes.SET_ALERT_VOLUME:
      return {
        ...state,
        ui: {
          ...state.ui,
          esp32Alerts: {
            ...state.ui.esp32Alerts,
            alertVolume: action.payload
          }
        }
      };
      
    case ActionTypes.SET_ONBOARDING_STEP:
      return {
        ...state,
        onboarding: {
          ...state.onboarding,
          currentStep: action.payload
        }
      };
      
    case ActionTypes.UPDATE_ASSESSMENT_DATA:
      return {
        ...state,
        onboarding: {
          ...state.onboarding,
          assessmentData: {
            ...state.onboarding.assessmentData,
            ...action.payload
          }
        }
      };
      
    case ActionTypes.COMPLETE_ONBOARDING:
      return {
        ...state,
        onboardingComplete: true,
        onboarding: {
          ...state.onboarding,
          isComplete: true
        }
      };
      
    case ActionTypes.RESET_ONBOARDING:
      return {
        ...state,
        onboarding: {
          ...initialState.onboarding
        }
      };
      
    default:
      return state;
  }
}

// Create context
const AppContext = createContext();

// Context provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  // Removed auto-cleanup timer to prevent performance issues
  // Errors and notifications will be manually cleared by user actions
  
  // Action creators
  const actions = {
    // Authentication actions
    setUser: (userData) => dispatch({ type: ActionTypes.SET_USER, payload: userData }),
    setLoading: (loading) => dispatch({ type: ActionTypes.SET_LOADING, payload: loading }),
    logout: () => dispatch({ type: ActionTypes.LOGOUT }),
    
    // Device actions
    setDeviceConnection: (connectionData) => dispatch({ type: ActionTypes.SET_DEVICE_CONNECTION, payload: connectionData }),
    updateDeviceStatus: (statusData) => dispatch({ type: ActionTypes.UPDATE_DEVICE_STATUS, payload: statusData }),
    setCalibrationStatus: (status) => dispatch({ type: ActionTypes.SET_CALIBRATION_STATUS, payload: status }),
    
    // Demo mode actions
    startDemoMode: (deviceId, scenario) => dispatch({ type: ActionTypes.START_DEMO_MODE, payload: { deviceId, scenario } }),
    stopDemoMode: () => dispatch({ type: ActionTypes.STOP_DEMO_MODE }),
    updateDemoStatus: (statusData) => dispatch({ type: ActionTypes.UPDATE_DEMO_STATUS, payload: statusData }),
    setDemoScenario: (scenario) => dispatch({ type: ActionTypes.SET_DEMO_SCENARIO, payload: scenario }),
    
    // ESP32 Integration actions
    setESP32Connection: (connectionData) => dispatch({ type: ActionTypes.SET_ESP32_CONNECTION, payload: connectionData }),
    updateESP32Status: (statusData) => dispatch({ type: ActionTypes.UPDATE_ESP32_STATUS, payload: statusData }),
    setESP32DemoMode: (enabled) => dispatch({ type: ActionTypes.SET_ESP32_DEMO_MODE, payload: enabled }),
    
    // Clinical Analytics actions
    setPusherDetected: (detected, score) => dispatch({ type: ActionTypes.SET_PUSHER_DETECTED, payload: { detected, score } }),
    updateClinicalScore: (score) => dispatch({ type: ActionTypes.UPDATE_CLINICAL_SCORE, payload: score }),
    setClinicalThresholds: (thresholds) => dispatch({ type: ActionTypes.SET_CLINICAL_THRESHOLDS, payload: thresholds }),
    addEpisode: (episode) => dispatch({ type: ActionTypes.ADD_EPISODE, payload: episode }),
    updateResistanceIndex: (index) => dispatch({ type: ActionTypes.UPDATE_RESISTANCE_INDEX, payload: index }),
    updateCorrectionAttempts: (attempts) => dispatch({ type: ActionTypes.UPDATE_CORRECTION_ATTEMPTS, payload: attempts }),
    updateClinicalConfidence: (confidence) => dispatch({ type: ActionTypes.UPDATE_CLINICAL_CONFIDENCE, payload: confidence }),
    
    // Calibration actions
    updateCalibrationProgress: (progress) => dispatch({ type: ActionTypes.UPDATE_CALIBRATION_PROGRESS, payload: progress }),
    setCalibrationBaseline: (baseline) => dispatch({ type: ActionTypes.SET_CALIBRATION_BASELINE, payload: baseline }),
    setCalibrationDevice: (deviceId) => dispatch({ type: ActionTypes.SET_CALIBRATION_DEVICE, payload: deviceId }),
    setCalibrationActive: (isActive) => dispatch({ type: ActionTypes.SET_CALIBRATION_ACTIVE, payload: isActive }),
    
    // Monitoring actions
    startMonitoring: (sessionId) => dispatch({ type: ActionTypes.START_MONITORING, payload: { sessionId } }),
    stopMonitoring: () => dispatch({ type: ActionTypes.STOP_MONITORING }),
    updateLivePosture: (postureData) => dispatch({ type: ActionTypes.UPDATE_LIVE_POSTURE, payload: postureData }),
    setAlertLevel: (level) => dispatch({ type: ActionTypes.SET_ALERT_LEVEL, payload: level }),
    
    // UI actions
    setCurrentPage: (page) => dispatch({ type: ActionTypes.SET_CURRENT_PAGE, payload: page }),
    setUILoading: (loading) => dispatch({ type: ActionTypes.SET_UI_LOADING, payload: loading }),
    addError: (message, type = 'error') => dispatch({ type: ActionTypes.ADD_ERROR, payload: { message, type } }),
    removeError: (id) => dispatch({ type: ActionTypes.REMOVE_ERROR, payload: id }),
    addNotification: (message, type = 'info') => dispatch({ type: ActionTypes.ADD_NOTIFICATION, payload: { message, type } }),
    removeNotification: (id) => dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: id }),
    
    // ESP32 Alert Management actions
    setESP32AlertPreferences: (preferences) => dispatch({ type: ActionTypes.SET_ESP32_ALERT_PREFERENCES, payload: preferences }),
    toggleESP32AlertType: (alertType) => dispatch({ type: ActionTypes.TOGGLE_ESP32_ALERT_TYPE, payload: alertType }),
    setAlertVolume: (volume) => dispatch({ type: ActionTypes.SET_ALERT_VOLUME, payload: volume }),
    
    // Onboarding actions
    setOnboardingStep: (step) => dispatch({ type: ActionTypes.SET_ONBOARDING_STEP, payload: step }),
    updateAssessmentData: (data) => dispatch({ type: ActionTypes.UPDATE_ASSESSMENT_DATA, payload: data }),
    completeOnboarding: () => dispatch({ type: ActionTypes.COMPLETE_ONBOARDING }),
    resetOnboarding: () => dispatch({ type: ActionTypes.RESET_ONBOARDING })
  };
  
  const value = {
    state,
    actions
  };
  
  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the app context
export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

export default AppContext;