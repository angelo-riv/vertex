import React from 'react';

const AlertMessage = ({ 
  alertLevel = 'safe', // 'safe', 'warning', 'unsafe'
  message = '',
  tiltAngle = 0,
  direction = 'center',
  onDismiss = null,
  autoHide = false,
  duration = 5000
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
      case 'safe':
      default:
        return 'Posture is within safe range. Good job maintaining proper alignment!';
    }
  };

  const displayMessage = getDefaultMessage();

  // Get priority level for screen readers
  const getAriaLive = () => {
    switch (alertLevel) {
      case 'unsafe':
        return 'assertive';
      case 'warning':
        return 'polite';
      case 'safe':
      default:
        return 'polite';
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
          {alertLevel === 'unsafe' ? 'Unsafe Posture' : 
           alertLevel === 'warning' ? 'Posture Warning' : 
           'Good Posture'}
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