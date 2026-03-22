/**
 * Connection Status Widget
 * 
 * Compact connection status display for use in headers, sidebars, or status bars.
 * Shows ESP32 connection, data freshness, and internet connectivity at a glance.
 * 
 * Requirements implemented:
 * - 7.2: Display connection status with device status and data freshness
 * - 7.4: Show "Device Disconnected" message with last update time
 * - Maintain internet connectivity indicators separate from ESP32 status
 */

import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import useConnectionStatus from '../../hooks/useConnectionStatus';

const ConnectionStatusWidget = ({ 
  size = 'medium', // 'small', 'medium', 'large'
  showLabels = true,
  showInternetStatus = true,
  onClick = null,
  className = ''
}) => {
  const { state } = useApp();
  const { esp32, demo } = state;
  
  const {
    isConnected,
    quality: connectionQuality,
    lastDataTime,
    deviceId,
    shouldSuggestDemo
  } = useConnectionStatus();

  const [internetConnected, setInternetConnected] = useState(true);

  // Monitor internet connectivity
  useEffect(() => {
    const checkInternet = async () => {
      try {
        await fetch('https://httpbin.org/status/200', { 
          method: 'HEAD', 
          mode: 'no-cors',
          signal: AbortSignal.timeout(3000)
        });
        setInternetConnected(true);
      } catch {
        setInternetConnected(false);
      }
    };

    checkInternet();
    const interval = setInterval(checkInternet, 30000);
    return () => clearInterval(interval);
  }, []);

  // Size-based styling
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          container: 'px-2 py-1',
          text: 'text-xs',
          icon: 'text-xs',
          gap: 'gap-1'
        };
      case 'large':
        return {
          container: 'px-4 py-3',
          text: 'text-base',
          icon: 'text-lg',
          gap: 'gap-3'
        };
      default: // medium
        return {
          container: 'px-3 py-2',
          text: 'text-sm',
          icon: 'text-sm',
          gap: 'gap-2'
        };
    }
  };

  // Get connection status info
  const getStatusInfo = () => {
    if (demo.isActive) {
      return {
        color: '#8b5cf6',
        bgColor: '#f3e8ff',
        icon: '▶️',
        text: 'Demo',
        detail: 'Simulated data'
      };
    }

    if (isConnected) {
      const dataAge = lastDataTime ? (new Date() - new Date(lastDataTime)) / 1000 : Infinity;
      
      if (dataAge < 5) {
        return {
          color: '#10b981',
          bgColor: '#d1fae5',
          icon: '●',
          text: 'Connected',
          detail: 'Live data'
        };
      } else if (dataAge < 30) {
        return {
          color: '#f59e0b',
          bgColor: '#fef3c7',
          icon: '⚠️',
          text: 'Issues',
          detail: `${Math.floor(dataAge)}s ago`
        };
      }
    }

    return {
      color: '#ef4444',
      bgColor: '#fee2e2',
      icon: '●',
      text: 'Disconnected',
      detail: shouldSuggestDemo ? 'Try demo' : 'No device'
    };
  };

  // Format time for tooltip
  const formatLastUpdate = () => {
    if (!lastDataTime) return 'No data received';
    
    const now = new Date();
    const diff = Math.floor((now - new Date(lastDataTime)) / 1000);
    
    if (diff < 60) return `Last update: ${diff}s ago`;
    if (diff < 3600) return `Last update: ${Math.floor(diff / 60)}m ago`;
    return `Last update: ${new Date(lastDataTime).toLocaleTimeString()}`;
  };

  const sizeStyles = getSizeStyles();
  const statusInfo = getStatusInfo();

  return (
    <div 
      className={`connection-status-widget ${className}`}
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        backgroundColor: statusInfo.bgColor,
        border: `1px solid ${statusInfo.color}`,
        borderRadius: 'var(--border-radius-md)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'var(--transition-fast)'
      }}
      title={formatLastUpdate()}
    >
      <div 
        className={`${sizeStyles.container} ${sizeStyles.gap}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          color: statusInfo.color
        }}
      >
        {/* ESP32 Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <span 
            className={sizeStyles.icon}
            style={{
              animation: isConnected && !demo.isActive ? 'pulse 2s infinite' : 'none'
            }}
          >
            {statusInfo.icon}
          </span>
          
          {showLabels && (
            <div>
              <div 
                className={sizeStyles.text}
                style={{
                  fontWeight: '600',
                  lineHeight: '1.2'
                }}
              >
                {statusInfo.text}
              </div>
              {size !== 'small' && (
                <div 
                  style={{
                    fontSize: size === 'large' ? '12px' : '10px',
                    opacity: 0.8,
                    lineHeight: '1.2'
                  }}
                >
                  {statusInfo.detail}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Connection Quality Bars */}
        {isConnected && !demo.isActive && size !== 'small' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1px',
            marginLeft: '8px'
          }}>
            {[1, 2, 3].map((bar) => (
              <div
                key={bar}
                style={{
                  width: size === 'large' ? '3px' : '2px',
                  height: `${(size === 'large' ? 8 : 6) + bar * 2}px`,
                  backgroundColor: bar <= (
                    connectionQuality === 'excellent' ? 3 : 
                    connectionQuality === 'good' ? 2 : 1
                  ) ? statusInfo.color : '#e5e7eb',
                  borderRadius: '1px'
                }}
              />
            ))}
          </div>
        )}

        {/* Internet Status Indicator */}
        {showInternetStatus && size !== 'small' && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginLeft: '8px',
            paddingLeft: '8px',
            borderLeft: `1px solid ${statusInfo.color}`,
            opacity: 0.7
          }}>
            <span 
              style={{
                fontSize: size === 'large' ? '14px' : '12px',
                color: internetConnected ? '#10b981' : '#ef4444'
              }}
              title={`Internet: ${internetConnected ? 'Connected' : 'Disconnected'}`}
            >
              🌐
            </span>
          </div>
        )}

        {/* Demo Mode Suggestion Indicator */}
        {shouldSuggestDemo && !demo.isActive && (
          <div style={{
            marginLeft: '8px',
            fontSize: size === 'large' ? '14px' : '12px',
            animation: 'blink 1s infinite'
          }}>
            💡
          </div>
        )}
      </div>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

export default ConnectionStatusWidget;