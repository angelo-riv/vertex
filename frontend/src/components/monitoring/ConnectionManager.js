/**
 * Connection Manager Component
 * 
 * Comprehensive connection management and fallback system for ESP32 integration.
 * Handles device connection status, data freshness, and demo mode suggestions.
 * 
 * Requirements implemented:
 * - 7.2: Display connection status with device status and data freshness
 * - 7.4: Show "Device Disconnected" message with last update time
 * - 7.7: Suggest demo mode switch after multiple connection failures
 * - Maintain internet connectivity indicators separate from ESP32 status
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import useWebSocket from '../../hooks/useWebSocket';

const ConnectionManager = ({ 
  className = '',
  showDetails = true,
  onDemoModeToggle = null,
  onRetryConnection = null 
}) => {
  const { state, actions } = useApp();
  const { esp32, demo, ui } = state;
  
  // Connection failure tracking
  const [connectionFailures, setConnectionFailures] = useState(0);
  const [lastFailureTime, setLastFailureTime] = useState(null);
  const [showDemoSuggestion, setShowDemoSuggestion] = useState(false);
  const [internetConnected, setInternetConnected] = useState(true);
  
  // WebSocket connection management
  const {
    isConnected: wsConnected,
    connectionStatus: wsStatus,
    reconnectAttempts,
    lastConnectionTime,
    lastDataTime,
    connectionQuality,
    connect: wsConnect,
    disconnect: wsDisconnect
  } = useWebSocket({ autoConnect: false });

  // Monitor internet connectivity separately from ESP32
  useEffect(() => {
    const checkInternetConnection = async () => {
      try {
        // Try to fetch a small resource to check internet connectivity
        const response = await fetch('https://httpbin.org/status/200', {
          method: 'HEAD',
          mode: 'no-cors',
          cache: 'no-cache'
        });
        setInternetConnected(true);
      } catch (error) {
        // Also check if we can reach our backend
        try {
          await fetch('http://localhost:8000/api/health', {
            method: 'HEAD',
            timeout: 3000
          });
          setInternetConnected(true);
        } catch (backendError) {
          setInternetConnected(false);
        }
      }
    };

    // Check internet connection on mount and periodically
    checkInternetConnection();
    const internetCheckInterval = setInterval(checkInternetConnection, 30000);

    return () => clearInterval(internetCheckInterval);
  }, []);

  // Track connection failures and suggest demo mode
  useEffect(() => {
    const deviceConnected = esp32.isConnected || wsConnected;
    
    if (!deviceConnected && !demo.isActive) {
      // Increment failure count if we're not in demo mode and device is disconnected
      const now = new Date();
      if (!lastFailureTime || (now - lastFailureTime) > 60000) { // Only count if > 1 minute since last failure
        setConnectionFailures(prev => prev + 1);
        setLastFailureTime(now);
      }
      
      // Show demo suggestion after 3 failures
      if (connectionFailures >= 2) {
        setShowDemoSuggestion(true);
      }
    } else if (deviceConnected || demo.isActive) {
      // Reset failure count when connected or in demo mode
      setConnectionFailures(0);
      setShowDemoSuggestion(false);
      setLastFailureTime(null);
    }
  }, [esp32.isConnected, wsConnected, demo.isActive, connectionFailures, lastFailureTime]);

  // Calculate data freshness
  const getDataFreshness = useCallback(() => {
    const lastUpdate = esp32.lastDataTimestamp || lastDataTime;
    if (!lastUpdate) return { text: 'No data', color: '#6b7280', urgent: true };
    
    const now = new Date();
    const diffSeconds = Math.floor((now - new Date(lastUpdate)) / 1000);
    
    if (diffSeconds < 5) {
      return { text: 'Live', color: '#10b981', urgent: false };
    } else if (diffSeconds < 30) {
      return { text: `${diffSeconds}s ago`, color: '#3b82f6', urgent: false };
    } else if (diffSeconds < 300) {
      return { text: `${Math.floor(diffSeconds / 60)}m ago`, color: '#f59e0b', urgent: true };
    } else {
      return { text: 'Stale data', color: '#ef4444', urgent: true };
    }
  }, [esp32.lastDataTimestamp, lastDataTime]);

  // Get overall connection status
  const getConnectionStatus = useCallback(() => {
    const deviceConnected = esp32.isConnected || wsConnected;
    const dataFreshness = getDataFreshness();
    
    if (demo.isActive) {
      return {
        status: 'demo',
        color: '#8b5cf6',
        bgColor: '#f3e8ff',
        icon: '▶️',
        title: 'Demo Mode Active',
        subtitle: 'Simulated data streaming',
        urgent: false
      };
    } else if (deviceConnected && !dataFreshness.urgent) {
      return {
        status: 'connected',
        color: '#10b981',
        bgColor: '#d1fae5',
        icon: '●',
        title: 'ESP32 Connected',
        subtitle: `Device: ${esp32.deviceId || 'Unknown'} • ${dataFreshness.text}`,
        urgent: false
      };
    } else if (deviceConnected && dataFreshness.urgent) {
      return {
        status: 'connected_stale',
        color: '#f59e0b',
        bgColor: '#fef3c7',
        icon: '⚠️',
        title: 'Connection Issues',
        subtitle: `Data ${dataFreshness.text} • Check device`,
        urgent: true
      };
    } else {
      return {
        status: 'disconnected',
        color: '#ef4444',
        bgColor: '#fee2e2',
        icon: '●',
        title: 'Device Disconnected',
        subtitle: esp32.lastDataTimestamp ? 
          `Last update: ${new Date(esp32.lastDataTimestamp).toLocaleTimeString()}` : 
          'No data received',
        urgent: true
      };
    }
  }, [esp32.isConnected, esp32.deviceId, esp32.lastDataTimestamp, wsConnected, demo.isActive, getDataFreshness]);

  // Handle demo mode toggle
  const handleDemoModeToggle = useCallback(async () => {
    try {
      if (onDemoModeToggle) {
        await onDemoModeToggle();
      } else {
        // Default demo mode toggle logic
        if (demo.isActive) {
          actions.stopDemoMode();
          actions.addNotification('Demo mode deactivated', 'info');
        } else {
          actions.startDemoMode('ESP32_DEMO_FALLBACK', 'normal_posture');
          actions.addNotification('Demo mode activated due to connection issues', 'warning');
        }
      }
      setShowDemoSuggestion(false);
    } catch (error) {
      console.error('Failed to toggle demo mode:', error);
      actions.addError('Failed to toggle demo mode', 'error');
    }
  }, [demo.isActive, onDemoModeToggle, actions]);

  // Handle connection retry
  const handleRetryConnection = useCallback(async () => {
    try {
      if (onRetryConnection) {
        await onRetryConnection();
      } else {
        // Default retry logic
        wsConnect();
        actions.addNotification('Attempting to reconnect...', 'info');
      }
    } catch (error) {
      console.error('Failed to retry connection:', error);
      actions.addError('Connection retry failed', 'error');
    }
  }, [onRetryConnection, wsConnect, actions]);

  const connectionStatus = getConnectionStatus();
  const dataFreshness = getDataFreshness();

  return (
    <div className={`connection-manager ${className}`}>
      {/* Main Connection Status Card */}
      <div 
        style={{
          backgroundColor: connectionStatus.bgColor,
          border: `1px solid ${connectionStatus.color}`,
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-4)',
          marginBottom: 'var(--spacing-3)'
        }}
      >
        {/* Status Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: showDetails ? 'var(--spacing-3)' : 0
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <span style={{
              fontSize: 'var(--font-size-lg)',
              animation: connectionStatus.status === 'connected' ? 'pulse 2s infinite' : 'none'
            }}>
              {connectionStatus.icon}
            </span>
            <div>
              <div style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: '600',
                color: connectionStatus.color,
                marginBottom: '2px'
              }}>
                {connectionStatus.title}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: connectionStatus.color,
                opacity: 0.8
              }}>
                {connectionStatus.subtitle}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{
            display: 'flex',
            gap: 'var(--spacing-2)'
          }}>
            {connectionStatus.status === 'disconnected' && (
              <button
                onClick={handleRetryConnection}
                style={{
                  padding: '6px 12px',
                  backgroundColor: 'white',
                  color: connectionStatus.color,
                  border: `1px solid ${connectionStatus.color}`,
                  borderRadius: 'var(--border-radius-md)',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'var(--transition-fast)'
                }}
              >
                Retry
              </button>
            )}
          </div>
        </div>

        {/* Detailed Information */}
        {showDetails && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: 'var(--spacing-3)',
            padding: 'var(--spacing-3)',
            backgroundColor: 'rgba(255, 255, 255, 0.5)',
            borderRadius: 'var(--border-radius-md)'
          }}>
            {/* WebSocket Status */}
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--gray-600)',
                marginBottom: '4px'
              }}>
                WebSocket
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                color: wsConnected ? '#10b981' : '#ef4444'
              }}>
                {wsConnected ? 'Connected' : 'Disconnected'}
              </div>
            </div>

            {/* Connection Quality */}
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--gray-600)',
                marginBottom: '4px'
              }}>
                Quality
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                color: dataFreshness.color
              }}>
                {esp32.connectionQuality || connectionQuality || 'Unknown'}
              </div>
            </div>

            {/* Internet Status */}
            <div style={{ textAlign: 'center' }}>
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--gray-600)',
                marginBottom: '4px'
              }}>
                Internet
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '500',
                color: internetConnected ? '#10b981' : '#ef4444'
              }}>
                {internetConnected ? 'Online' : 'Offline'}
              </div>
            </div>

            {/* Reconnect Attempts */}
            {reconnectAttempts > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--gray-600)',
                  marginBottom: '4px'
                }}>
                  Attempts
                </div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '500',
                  color: '#f59e0b'
                }}>
                  {reconnectAttempts}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Demo Mode Suggestion */}
      {showDemoSuggestion && !demo.isActive && (
        <div style={{
          backgroundColor: '#fef3c7',
          border: '1px solid #fcd34d',
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-4)',
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
              gap: 'var(--spacing-3)'
            }}>
              <div style={{
                fontSize: 'var(--font-size-lg)',
                color: '#f59e0b'
              }}>
                💡
              </div>
              <div>
                <div style={{
                  fontSize: 'var(--font-size-base)',
                  fontWeight: '600',
                  color: '#92400e',
                  marginBottom: '4px'
                }}>
                  Connection Issues Detected
                </div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  color: '#a16207'
                }}>
                  Multiple connection failures. Would you like to switch to demo mode?
                </div>
              </div>
            </div>
            
            <div style={{
              display: 'flex',
              gap: 'var(--spacing-2)'
            }}>
              <button
                onClick={() => setShowDemoSuggestion(false)}
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
                onClick={handleDemoModeToggle}
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
                Enable Demo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Internet Connectivity Notice */}
      {!internetConnected && (
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: 'var(--border-radius-lg)',
          padding: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <span style={{
              fontSize: 'var(--font-size-base)',
              color: '#dc2626'
            }}>
              🌐
            </span>
            <div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                fontWeight: '600',
                color: '#dc2626',
                marginBottom: '2px'
              }}>
                Internet Connection Lost
              </div>
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: '#991b1b'
              }}>
                Some features may be limited. ESP32 connection status is independent.
              </div>
            </div>
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

export default ConnectionManager;