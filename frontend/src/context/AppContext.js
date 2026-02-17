import React, { createContext, useContext, useReducer, useEffect } from 'react';

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
      hapticActive: false
    },
    alertLevel: 'safe'
  },
  
  // UI State
  ui: {
    currentPage: 'login',
    isLoading: false,
    errors: [],
    notifications: [],
    theme: 'light'
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