import React, { useEffect, useState } from 'react';
import { useApp } from '../../context/AppContext';
import AlertMessage from './AlertMessage';

/**
 * ESP32 Notification Manager
 * 
 * Integrates ESP32 features with existing alert and notification systems.
 * Manages ESP32 connection notifications, pusher detection alerts, 
 * clinical threshold breach notifications, and calibration reminders.
 * 
 * Requirements: 19.5, 19.6 - Integration with existing alert and authentication systems
 */
const ESP32NotificationManager = () => {
  const { state, actions } = useApp();
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [lastConnectionState, setLastConnectionState] = useState(null);
  const [lastPusherState, setLastPusherState] = useState(false);

  // Monitor ESP32 connection changes
  useEffect(() => {
    const currentConnectionState = state.esp32.isConnected;
    
    // Connection state changed
    if (lastConnectionState !== null && lastConnectionState !== currentConnectionState) {
      if (currentConnectionState) {
        // Device connected
        addAlert({
          id: `esp32_connection_${Date.now()}`,
          alertLevel: 'esp32_connection',
          esp32Status: state.esp32,
          autoHide: true,
          duration: 5000
        });
      } else {
        // Device disconnected
        addAlert({
          id: `esp32_disconnection_${Date.now()}`,
          alertLevel: 'esp32_disconnection',
          esp32Status: state.esp32,
          autoHide: true,
          duration: 10000
        });
      }
    }
    
    setLastConnectionState(currentConnectionState);
  }, [state.esp32.isConnected, state.esp32.deviceId]);

  // Monitor pusher syndrome detection
  useEffect(() => {
    const currentPusherState = state.clinical.pusherDetected;
    
    // Pusher syndrome detected (new episode)
    if (!lastPusherState && currentPusherState) {
      addAlert({
        id: `pusher_detected_${Date.now()}`,
        alertLevel: 'pusher_detected',
        tiltAngle: state.monitoring.livePosture.tiltAngle,
        direction: state.monitoring.livePosture.tiltDirection,
        clinicalData: state.clinical,
        autoHide: true,
        duration: 15000 // Longer duration for clinical alerts
      });
    }
    
    setLastPusherState(currentPusherState);
  }, [state.clinical.pusherDetected, state.clinical.clinicalScore]);

  // Monitor clinical threshold breaches
  useEffect(() => {
    const tiltAngle = Math.abs(state.monitoring.livePosture.tiltAngle);
    const severeThreshold = state.clinical.thresholds.severe;
    
    // Check for severe threshold breach
    if (tiltAngle >= severeThreshold && state.esp32.isConnected) {
      // Only show alert if not already showing one for threshold breach
      const hasThresholdAlert = activeAlerts.some(alert => 
        alert.alertLevel === 'threshold_breach' && 
        Date.now() - alert.timestamp < 30000 // Within last 30 seconds
      );
      
      if (!hasThresholdAlert) {
        addAlert({
          id: `threshold_breach_${Date.now()}`,
          alertLevel: 'threshold_breach',
          tiltAngle: state.monitoring.livePosture.tiltAngle,
          direction: state.monitoring.livePosture.tiltDirection,
          clinicalData: state.clinical,
          autoHide: true,
          duration: 10000
        });
      }
    }
  }, [state.monitoring.livePosture.tiltAngle, state.clinical.thresholds.severe]);

  // Monitor calibration status and reminders
  useEffect(() => {
    const calibrationStatus = state.calibration.status;
    const lastCalibrationDate = state.calibration.lastCalibrationDate;
    
    // Check if calibration is needed
    if (calibrationStatus === 'not_calibrated' && state.esp32.isConnected) {
      // Show calibration reminder if not already showing one
      const hasCalibrationAlert = activeAlerts.some(alert => 
        alert.alertLevel === 'calibration_reminder' && 
        Date.now() - alert.timestamp < 300000 // Within last 5 minutes
      );
      
      if (!hasCalibrationAlert) {
        addAlert({
          id: `calibration_reminder_${Date.now()}`,
          alertLevel: 'calibration_reminder',
          calibrationStatus: state.calibration,
          autoHide: true,
          duration: 20000 // Longer duration for calibration reminders
        });
      }
    }
    
    // Check if calibration is outdated (more than 7 days)
    if (lastCalibrationDate && state.esp32.isConnected) {
      const daysSinceCalibration = Math.floor(
        (new Date() - new Date(lastCalibrationDate)) / (1000 * 60 * 60 * 24)
      );
      
      if (daysSinceCalibration > 7) {
        const hasOutdatedCalibrationAlert = activeAlerts.some(alert => 
          alert.alertLevel === 'calibration_reminder' && 
          Date.now() - alert.timestamp < 3600000 // Within last hour
        );
        
        if (!hasOutdatedCalibrationAlert) {
          addAlert({
            id: `calibration_outdated_${Date.now()}`,
            alertLevel: 'calibration_reminder',
            message: `Device calibration is ${daysSinceCalibration} days old. Consider recalibrating for optimal accuracy.`,
            calibrationStatus: state.calibration,
            autoHide: true,
            duration: 15000
          });
        }
      }
    }
  }, [state.calibration.status, state.calibration.lastCalibrationDate, state.esp32.isConnected]);

  // Add alert to active alerts list
  const addAlert = (alert) => {
    const alertWithTimestamp = {
      ...alert,
      timestamp: Date.now()
    };
    
    setActiveAlerts(prev => {
      // Remove any existing alerts of the same type to prevent duplicates
      const filtered = prev.filter(existingAlert => 
        existingAlert.alertLevel !== alert.alertLevel
      );
      
      // Add new alert
      return [...filtered, alertWithTimestamp];
    });

    // Also add to global notification system
    actions.addNotification(
      getNotificationMessage(alert.alertLevel, alert),
      getNotificationType(alert.alertLevel)
    );
  };

  // Remove alert from active alerts list
  const removeAlert = (alertId) => {
    setActiveAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  // Get notification message for global notification system
  const getNotificationMessage = (alertLevel, alert) => {
    switch (alertLevel) {
      case 'esp32_connection':
        return `ESP32 device connected: ${alert.esp32Status?.deviceId || 'Unknown'}`;
      case 'esp32_disconnection':
        return 'ESP32 device disconnected. Check device power and WiFi.';
      case 'pusher_detected':
        return `Pusher syndrome detected - Severity: ${getClinicalSeverityLabel(alert.clinicalData?.clinicalScore)}`;
      case 'calibration_reminder':
        return 'Device calibration required for accurate detection';
      case 'threshold_breach':
        return `Clinical threshold exceeded: ${alert.tiltAngle?.toFixed(1)}°`;
      default:
        return 'ESP32 notification';
    }
  };

  // Get notification type for global notification system
  const getNotificationType = (alertLevel) => {
    switch (alertLevel) {
      case 'esp32_connection':
        return 'success';
      case 'esp32_disconnection':
      case 'pusher_detected':
      case 'threshold_breach':
        return 'error';
      case 'calibration_reminder':
        return 'warning';
      default:
        return 'info';
    }
  };

  // Helper function for clinical severity labels
  const getClinicalSeverityLabel = (score) => {
    switch (score) {
      case 0: return 'No Pushing';
      case 1: return 'Mild';
      case 2: return 'Moderate';
      case 3: return 'Severe';
      default: return 'Unknown';
    }
  };

  // Auto-hide alerts after their duration
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      setActiveAlerts(prev => 
        prev.filter(alert => {
          if (alert.autoHide && now - alert.timestamp > alert.duration) {
            return false;
          }
          return true;
        })
      );
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      position: 'fixed',
      top: 'var(--spacing-4)',
      right: 'var(--spacing-4)',
      zIndex: 1000,
      maxWidth: '400px',
      width: '100%'
    }}>
      {activeAlerts.map(alert => (
        <div key={alert.id} style={{ marginBottom: 'var(--spacing-2)' }}>
          <AlertMessage
            alertLevel={alert.alertLevel}
            message={alert.message}
            tiltAngle={alert.tiltAngle}
            direction={alert.direction}
            esp32Status={alert.esp32Status || state.esp32}
            clinicalData={alert.clinicalData || state.clinical}
            calibrationStatus={alert.calibrationStatus || state.calibration}
            onDismiss={() => removeAlert(alert.id)}
            autoHide={alert.autoHide}
            duration={alert.duration}
          />
        </div>
      ))}
    </div>
  );
};

export default ESP32NotificationManager;