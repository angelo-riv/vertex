import React from 'react';

const AlertMessage = ({ 
  alertLevel = 'safe', // 'safe', 'warning', 'unsafe', 'esp32_connection', 'esp32_disconnection', 'pusher_detected', 'calibration_reminder', 'threshold_breach'
  message = '',
  tiltAngle = 0,
  direction = 'center',
  onDismiss = null,
  autoHide = false,
  duration = 5000,
  // ESP32 Integration props
  esp32Status = {
    isConnected: false,
    deviceId: null,
    connectionQuality: 'unknown',
    demoMode: false
  },
  // Clinical Analytics props
  clinicalData = {
    pusherDetected: false,
    clinicalScore: 0,
    confidence: 0,
    episodeCount: 0
  },
  // Calibration props
  calibrationStatus = {
    status: 'not_calibrated',
    lastCalibrationDate: null
  }
}) => {
  // Auto-hide functionality
  React.useEffect(() => {
    if (autoHide && alertLevel !== 'safe' && onDismiss) {
      const timer = setTimeout(() => {
        onDismiss();
      }, duration);
      
      return () => clearTimeout(timer);
    }
  }, [autoHide, alertLevel, onDismiss, duration]);

  // Don't render if safe and no custom message
  if (alertLevel === 'safe' && !message) {
    return null;
  }

  // Get alert styling based on level
  const getAlertStyles = () => {
    switch (alertLevel) {
      case 'unsafe':
        return {
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          textColor: '#dc2626',
          iconColor: '#dc2626',
          icon: '⚠'
        };
      case 'warning':
        return {
          backgroundColor: '#fefbf2',
          borderColor: '#fde68a',
          textColor: '#d97706',
          iconColor: '#f59e0b',
          icon: '⚠'
        };
      case 'esp32_connection':
        return {
          backgroundColor: '#f0fdf4',
          borderColor: '#bbf7d0',
          textColor: '#166534',
          iconColor: '#10b981',
          icon: '📡'
        };
      case 'esp32_disconnection':
        return {
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          textColor: '#dc2626',
          iconColor: '#ef4444',
          icon: '📡'
        };
      case 'pusher_detected':
        return {
          backgroundColor: '#fef2f2',
          borderColor: '#fecaca',
          textColor: '#dc2626',
          iconColor: '#dc2626',
          icon: '🚨'
        };
      case 'calibration_reminder':
        return {
          backgroundColor: '#fffbeb',
          borderColor: '#fed7aa',
          textColor: '#c2410c',
          iconColor: '#f97316',
          icon: '⚙️'
        };
      case 'threshold_breach':
        return {
          backgroundColor: '#fef3c7',
          borderColor: '#fcd34d',
          textColor: '#92400e',
          iconColor: '#f59e0b',
          icon: '📊'
        };
      case 'safe':
      default:
        return {
          backgroundColor: 'var(--primary-blue-50)',
          borderColor: 'var(--primary-blue-200)',
          textColor: 'var(--primary-blue-700)',
          iconColor: 'var(--primary-blue)',
          icon: '✓'
        };
    }
  };

  const styles = getAlertStyles();

  // Generate default message if none provided
  const getDefaultMessage = () => {
    if (message) return message;
    
    switch (alertLevel) {
      case 'unsafe':
        return `Unsafe posture detected! Tilt angle: ${tiltAngle.toFixed(1)}° ${direction}. Please adjust your position.`;
      case 'warning':
        return `Posture warning: Tilt angle: ${tiltAngle.toFixed(1)}° ${direction}. Consider adjusting your position.`;
      case 'esp32_connection':
        return `ESP32 device connected successfully. Device ID: ${esp32Status.deviceId || 'Unknown'}. Connection quality: ${esp32Status.connectionQuality}.`;
      case 'esp32_disconnection':
        return `ESP32 device disconnected. Last seen: ${esp32Status.lastDataTimestamp ? new Date(esp32Status.lastDataTimestamp).toLocaleTimeString() : 'Unknown'}. Check device power and WiFi connection.`;
      case 'pusher_detected':
        return `Pusher syndrome episode detected! Severity: ${getClinicalSeverityLabel(clinicalData.clinicalScore)}. Confidence: ${(clinicalData.confidence * 100).toFixed(0)}%. Please assist patient with posture correction.`;
      case 'calibration_reminder':
        return `Device calibration ${calibrationStatus.lastCalibrationDate ? 'is outdated' : 'required'}. ${calibrationStatus.lastCalibrationDate ? `Last calibrated: ${formatCalibrationDate(calibrationStatus.lastCalibrationDate)}.` : ''} Please perform calibration for accurate detection.`;
      case 'threshold_breach':
        return `Clinical threshold exceeded. Current tilt: ${tiltAngle.toFixed(1)}°. Patient may require immediate attention and posture assistance.`;
      case 'safe':
      default:
        return 'Posture is within safe range. Good job maintaining proper alignment!';
    }
  };

  // Helper functions for ESP32 alert messages
  const getClinicalSeverityLabel = (score) => {
    switch (score) {
      case 0: return 'No Pushing';
      case 1: return 'Mild';
      case 2: return 'Moderate';
      case 3: return 'Severe';
      default: return 'Unknown';
    }
  };

  const formatCalibrationDate = (date) => {
    if (!date) return 'Never';
    const calibrationDate = new Date(date);
    const now = new Date();
    const diffDays = Math.floor((now - calibrationDate) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return calibrationDate.toLocaleDateString();
  };

  const displayMessage = getDefaultMessage();

  // Get priority level for screen readers
  const getAriaLive = () => {
    switch (alertLevel) {
      case 'unsafe':
      case 'pusher_detected':
      case 'threshold_breach':
        return 'assertive';
      case 'warning':
      case 'esp32_disconnection':
      case 'calibration_reminder':
        return 'polite';
      case 'safe':
      case 'esp32_connection':
      default:
        return 'polite';
    }
  };

  // Get alert title based on level
  const getAlertTitle = () => {
    switch (alertLevel) {
      case 'unsafe':
        return 'Unsafe Posture';
      case 'warning':
        return 'Posture Warning';
      case 'esp32_connection':
        return 'Device Connected';
      case 'esp32_disconnection':
        return 'Device Disconnected';
      case 'pusher_detected':
        return 'Pusher Syndrome Alert';
      case 'calibration_reminder':
        return 'Calibration Required';
      case 'threshold_breach':
        return 'Clinical Threshold Exceeded';
      case 'safe':
      default:
        return 'Good Posture';
    }
  };

  return (
    <div
      style={{
        backgroundColor: styles.backgroundColor,
        border: `2px solid ${styles.borderColor}`,
        borderRadius: 'var(--border-radius-lg)',
        padding: 'var(--spacing-4)',
        margin: 'var(--spacing-2) 0',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 'var(--spacing-3)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
        animation: alertLevel !== 'safe' ? 'slideIn 0.3s ease-out' : 'none'
      }}
      role="alert"
      aria-live={getAriaLive()}
      aria-atomic="true"
    >
      {/* Alert Icon */}
      <div style={{
        width: '24px',
        height: '24px',
        borderRadius: '50%',
        backgroundColor: styles.iconColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        marginTop: '2px'
      }}>
        <span style={{
          color: 'white',
          fontSize: 'var(--font-size-sm)',
          fontWeight: '700'
        }}>
          {alertLevel === 'unsafe' ? '!' : alertLevel === 'warning' ? '!' : '✓'}
        </span>
      </div>

      {/* Alert Content */}
      <div style={{ flex: 1 }}>
        <div style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: styles.textColor,
          marginBottom: 'var(--spacing-1)',
          lineHeight: '1.4'
        }}>
          {getAlertTitle()}
        </div>
        
        <div style={{
          fontSize: 'var(--font-size-sm)',
          color: styles.textColor,
          lineHeight: '1.5',
          opacity: 0.9
        }}>
          {displayMessage}
        </div>

        {/* Additional details for unsafe/warning states */}
        {(alertLevel === 'unsafe' || alertLevel === 'warning') && (
          <div style={{
            marginTop: 'var(--spacing-2)',
            padding: 'var(--spacing-2)',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            color: styles.textColor,
            fontWeight: '500'
          }}>
            Recommended: Slowly adjust your position to reduce tilt angle below 8°
          </div>
        )}

        {/* ESP32 connection details */}
        {alertLevel === 'esp32_connection' && esp32Status.demoMode && (
          <div style={{
            marginTop: 'var(--spacing-2)',
            padding: 'var(--spacing-2)',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            color: styles.textColor,
            fontWeight: '500'
          }}>
            Note: Demo mode is active. Switch to live hardware for real patient monitoring.
          </div>
        )}

        {/* Pusher syndrome episode details */}
        {alertLevel === 'pusher_detected' && (
          <div style={{
            marginTop: 'var(--spacing-2)',
            padding: 'var(--spacing-2)',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            color: styles.textColor,
            fontWeight: '500'
          }}>
            Episode #{clinicalData.episodeCount} today. Provide gentle guidance and support for posture correction.
          </div>
        )}

        {/* Calibration reminder details */}
        {alertLevel === 'calibration_reminder' && (
          <div style={{
            marginTop: 'var(--spacing-2)',
            padding: 'var(--spacing-2)',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            color: styles.textColor,
            fontWeight: '500'
          }}>
            Calibration improves detection accuracy. Press the calibration button on the device or use the app controls.
          </div>
        )}
      </div>

      {/* Dismiss Button */}
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: styles.textColor,
            cursor: 'pointer',
            padding: 'var(--spacing-1)',
            borderRadius: 'var(--border-radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '24px',
            height: '24px',
            opacity: 0.7,
            transition: 'opacity 0.2s ease'
          }}
          onMouseOver={(e) => e.target.style.opacity = '1'}
          onMouseOut={(e) => e.target.style.opacity = '0.7'}
          aria-label="Dismiss alert"
        >
          ×
        </button>
      )}

      {/* Slide-in animation */}
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateY(-10px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
};

export default AlertMessage;