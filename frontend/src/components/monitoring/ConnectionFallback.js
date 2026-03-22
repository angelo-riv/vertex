/**
 * Connection Fallback Component
 * 
 * Handles connection failures and provides fallback options including demo mode suggestions.
 * Displays connection status, last update times, and internet connectivity separately.
 * 
 * Requirements implemented:
 * - 7.2: Display connection status with device status and data freshness
 * - 7.4: Show "Device Disconnected" message with last update time
 * - 7.7: Suggest demo mode switch after multiple connection failures
 * - Maintain internet connectivity indicators separate from ESP32 status
 */

import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import useConnectionStatus from '../../hooks/useConnectionStatus';

const ConnectionFallback = ({ 
  onDemoModeActivate = null,
  onRetryConnection = null,
  className = '',
  showInternetStatus = true 
}) => {
  const { state, actions } = useApp();
  const { esp32, demo } = state;
  
  const {
    isConnected,
    quality: connectionQuality,
    lastDataTime,
    deviceId,
    connectionFailures,
    shouldSuggestDemo,
    diagnosticInfo,
    retryConnection,
    dismissDemoSuggestion
  } = useConnectionStatus({
    timeoutThreshold: 5000,
    failureThreshold: 3,
    autoSuggestDemo: true
  });

  const [internetStatus, setInternetStatus] = useState('checking');
  const [lastInternetCheck, setLastInternetCheck] = useState(null);

  // Check internet connectivity independently
  useEffect(() => {
    const checkInternetConnectivity = async () => {
      try {
        // Try multiple endpoints to verify internet connectivity
        const checks = [
          fetch('https://httpbin.org/status/200', { 
            method: 'HEAD', 
            mode: 'no-cors',
            cache: 'no-cache',
            signal: AbortSignal.timeout(5000)
          }),
          fetch('http://localhost:8000/api/health', {
            method: 'HEAD',
            signal: AbortSignal.timeout(3000)
          })
        ];

        const results = await Promise.allSettled(checks);
        const hasInternet = results.some(result => result.status === 'fulfilled');
        
        setInternetStatus(hasInternet ? 'connected' : 'disconnected');
        setLastInternetCheck(new Date());
      } catch (error) {
        setInternetStatus('disconnected');
        setLastInternetCheck(new Date());
      }
    };

    // Initial check
    checkInternetConnectivity();
    
    // Periodic checks every 30 seconds
    const interval = setInterval(checkInternetConnectivity, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Format time display
  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return 'Never';
    
    const now = new Date();
    const diff = Math.floor((now - new Date(timestamp)) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  // Get connection status display info
  const getConnectionDisplayInfo = () => {
    if (demo.isActive) {
      return {
        status: 'demo',
        color: '#8b5cf6',
        bgColor: '#f3e8ff',
        borderColor: '#c4b5fd',
        icon: '▶️',
        title: 'Demo Mode Active',
        subtitle: 'Simulated sensor data streaming',
        showActions: false
      };
    }

    if (isConnected) {
      const dataAge = lastDataTime ? (new Date() - new Date(lastDataTime)) / 1000 : Infinity;
      
      if (dataAge < 5) {
        return {
          status: 'connected',
          color: '#10b981',
          bgColor: '#d1fae5',
          borderColor: '#6ee7b7',
          icon: '●',
          title: 'ESP32 Connected',
          subtitle: `Device: ${deviceId || 'Unknown'} • Live data`,
          showActions: false
        };
      } else if (dataAge < 30) {
        return {
          status: 'connected_stale',
          color: '#f59e0b',
          bgColor: '#fef3c7',
          borderColor: '#fcd34d',
          icon: '⚠️',
          title: 'Connection Issues',
          subtitle: `Data ${formatTimeAgo(lastDataTime)} • Check device`,
          showActions: true
        };
      }
    }

    return {
      status: 'disconnected',
      color: '#ef4444',
      bgColor: '#fee2e2',
      borderColor: '#fca5a5',
      icon: '●',
      title: 'Device Disconnected',
      subtitle: lastDataTime ? 
        `Last update: ${formatTimeAgo(lastDataTime)}` : 
        'No data received from ESP32 device',
      showActions: true
    };
  };

  // Handle demo mode activation
  const handleDemoModeActivate = async () => {
    try {
      if (onDemoModeActivate) {
        await onDemoModeActivate();
      } else {
        // Default demo mode activation
        const response = await fetch('http://localhost:8000/api/demo/toggle?enabled=true&device_id=ESP32_FALLBACK', {
          method: 'POST'
        });

        if (response.ok) {
          actions.startDemoMode('ESP32_FALLBACK', 'normal_posture');
          actions.addNotification('Demo mode activated due to connection issues', 'success');
          dismissDemoSuggestion();
        } else {
          throw new Error('Failed to activate demo mode');
        }
      }
    } catch (error) {
      console.error('Failed to activate demo mode:', error);
      actions.addError('Failed to activate demo mode', 'error');
    }
  };

  // Handle connection retry
  const handleRetryConnection = async () => {
    try {
      if (onRetryConnection) {
        await onRetryConnection();
      } else {
        await retryConnection();
      }
    } catch (error) {
      console.error('Connection retry failed:', error);
      actions.addError('Connection retry failed', 'error');
    }
  };

  const connectionInfo = getConnectionDisplayInfo();

  return (
    <div className={`connection-fallback ${className}`}>
      {/* Main Connection Status */}
      <div 
        style={{
          backgroundColor: connectionInfo.bgColor,
          border: `2px solid ${connectionInfo.borderColor}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-4)',
          marginBottom: 'var(--spacing-3)'
        }}
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: connectionInfo.showActions ? 'var(--spacing-3)' : 0
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-3)'
          }}>
            <div style={{
              fontSize: '24px',
              animation: connectionInfo.status === 'connected' ? 'pulse 2s infinite' : 'none'
            }}>
              {connectionInfo.icon}
            </div>
            <div>
              <div style={{
                fontSize: 'var(--font-size-lg)',
                fontWeight: '700',
                color: connectionInfo.color,
                marginBottom: '4px'
              }}>
                {connectionInfo.title}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: connectionInfo.color,
                opacity: 0.8
              }}>
                {connectionInfo.subtitle}
              </div>
            </div>
          </div>

          {/* Connection Quality Indicator */}
          {isConnected && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px'
            }}>
              <div style={{
                display: 'flex',
                gap: '2px'
              }}>
                {[1, 2, 3].map((bar) => (
                  <div
                    key={bar}
                    style={{
                      width: '4px',
                      height: `${8 + bar * 2}px`,
                      backgroundColor: bar <= (connectionQuality === 'excellent' ? 3 : connectionQuality === 'good' ? 2 : 1) 
                        ? connectionInfo.color : '#e5e7eb',
                      borderRadius: '2px'
                    }}
                  />
                ))}
              </div>
              <div style={{
                fontSize: '10px',
                color: connectionInfo.color,
                fontWeight: '500',
                textTransform: 'capitalize'
              }}>
                {connectionQuality}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {connectionInfo.showActions && (
          <div style={{
            display: 'flex',
            gap: 'var(--spacing-2)',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={handleRetryConnection}
              style={{
                padding: '8px 16px',
                backgroundColor: 'white',
                color: connectionInfo.color,
                border: `1px solid ${connectionInfo.color}`,
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'var(--transition-fast)'
              }}
            >
              🔄 Retry Connection
            </button>

            {connectionFailures >= 2 && !demo.isActive && (
              <button
                onClick={handleDemoModeActivate}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#8b5cf6',
                  color: 'white',
                  border: 'none',
                  borderRadius: 'var(--border-radius-md)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'var(--transition-fast)'
                }}
              >
                ▶️ Enable Demo Mode
              </button>
            )}
          </div>
        )}
      </div>

      {/* Demo Mode Suggestion */}
      {shouldSuggestDemo && !demo.isActive && (
        <div style={{
          backgroundColor: '#fef3c7',
          border: '2px solid #fcd34d',
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-4)',
          marginBottom: 'var(--spacing-3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 'var(--spacing-2)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-3)'
            }}>
              <div style={{ fontSize: '24px' }}>💡</div>
              <div>
                <div style={{
                  fontSize: 'var(--font-size-base)',
                  fontWeight: '700',
                  color: '#92400e',
                  marginBottom: '4px'
                }}>
                  Multiple Connection Failures Detected
                </div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  color: '#a16207'
                }}>
                  {connectionFailures} failed attempts. Consider switching to demo mode for uninterrupted presentation.
                </div>
              </div>
            </div>
          </div>
          
          <div style={{
            display: 'flex',
            gap: 'var(--spacing-2)',
            justifyContent: 'flex-end'
          }}>
            <button
              onClick={dismissDemoSuggestion}
              style={{
                padding: '6px 12px',
                backgroundColor: 'transparent',
                color: '#92400e',
                border: '1px solid #fcd34d',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-sm)',
                cursor: 'pointer'
              }}
            >
              Dismiss
            </button>
            <button
              onClick={handleDemoModeActivate}
              style={{
                padding: '6px 12px',
                backgroundColor: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Enable Demo Mode
            </button>
          </div>
        </div>
      )}

      {/* Internet Connectivity Status (Separate from ESP32) */}
      {showInternetStatus && (
        <div style={{
          backgroundColor: internetStatus === 'connected' ? '#f0f9ff' : '#fef2f2',
          border: `1px solid ${internetStatus === 'connected' ? '#bae6fd' : '#fecaca'}`,
          borderRadius: 'var(--border-radius-md)',
          padding: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)'
            }}>
              <span style={{
                fontSize: 'var(--font-size-base)',
                color: internetStatus === 'connected' ? '#0369a1' : '#dc2626'
              }}>
                🌐
              </span>
              <div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '600',
                  color: internetStatus === 'connected' ? '#0369a1' : '#dc2626',
                  marginBottom: '2px'
                }}>
                  Internet: {internetStatus === 'connected' ? 'Connected' : 'Disconnected'}
                </div>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: internetStatus === 'connected' ? '#0284c7' : '#991b1b'
                }}>
                  {internetStatus === 'connected' 
                    ? 'Supabase and external services available'
                    : 'Limited functionality - ESP32 connection independent'
                  }
                </div>
              </div>
            </div>
            
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)'
            }}>
              {lastInternetCheck ? formatTimeAgo(lastInternetCheck) : 'Checking...'}
            </div>
          </div>
        </div>
      )}

      {/* Diagnostic Information */}
      {diagnosticInfo && (
        <div style={{
          backgroundColor: '#f3f4f6',
          border: '1px solid #d1d5db',
          borderRadius: 'var(--border-radius-md)',
          padding: 'var(--spacing-3)'
        }}>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: '600',
            color: 'var(--gray-700)',
            marginBottom: 'var(--spacing-1)'
          }}>
            Diagnostic Information
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--gray-600)',
            fontFamily: 'monospace'
          }}>
            {diagnosticInfo.message} ({formatTimeAgo(diagnosticInfo.timestamp)})
          </div>
        </div>
      )}

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
};

export default ConnectionFallback;