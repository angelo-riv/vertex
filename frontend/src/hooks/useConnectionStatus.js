/**
 * useConnectionStatus Hook
 * 
 * Centralized connection status management for ESP32 and WebSocket connections.
 * Provides connection quality assessment, failure tracking, and fallback suggestions.
 * 
 * Requirements implemented:
 * - 7.1: Track device connectivity status and last communication timestamps
 * - 7.3: Detect connection timeouts and update status
 * - 7.5: Automatically update status when transmission resumes
 * - 7.6: Provide diagnostic information for network errors
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import useWebSocket from './useWebSocket';

export const useConnectionStatus = (options = {}) => {
  const {
    timeoutThreshold = 5000, // 5 seconds timeout threshold
    failureThreshold = 3, // Number of failures before suggesting demo mode
    qualityCheckInterval = 10000, // Check connection quality every 10 seconds
    autoSuggestDemo = true
  } = options;

  const { state, actions } = useApp();
  const { esp32, demo } = state;

  // Connection state tracking
  const [connectionFailures, setConnectionFailures] = useState(0);
  const [lastFailureTime, setLastFailureTime] = useState(null);
  const [connectionQuality, setConnectionQuality] = useState('unknown');
  const [diagnosticInfo, setDiagnosticInfo] = useState(null);
  const [shouldSuggestDemo, setShouldSuggestDemo] = useState(false);

  // Refs for timeout tracking
  const timeoutRef = useRef(null);
  const qualityCheckRef = useRef(null);

  // WebSocket connection info
  const {
    isConnected: wsConnected,
    connectionStatus: wsStatus,
    lastDataTime: wsLastDataTime,
    reconnectAttempts
  } = useWebSocket({ autoConnect: false });

  /**
   * Calculate connection quality based on multiple factors
   */
  const calculateConnectionQuality = useCallback(() => {
    const now = new Date();
    const lastUpdate = esp32.lastDataTimestamp || wsLastDataTime;
    
    if (!lastUpdate) {
      return 'disconnected';
    }

    const timeSinceLastData = now - new Date(lastUpdate);
    const isESP32Connected = esp32.isConnected;
    const isWSConnected = wsConnected;

    // Quality assessment logic
    if (isESP32Connected && isWSConnected && timeSinceLastData < 2000) {
      return 'excellent';
    } else if ((isESP32Connected || isWSConnected) && timeSinceLastData < 5000) {
      return 'good';
    } else if ((isESP32Connected || isWSConnected) && timeSinceLastData < 15000) {
      return 'poor';
    } else {
      return 'disconnected';
    }
  }, [esp32.isConnected, esp32.lastDataTimestamp, wsConnected, wsLastDataTime]);

  /**
   * Get comprehensive connection status
   */
  const getConnectionStatus = useCallback(() => {
    const quality = calculateConnectionQuality();
    const lastUpdate = esp32.lastDataTimestamp || wsLastDataTime;
    const deviceConnected = esp32.isConnected || wsConnected;
    
    return {
      isConnected: deviceConnected,
      quality,
      lastDataTime: lastUpdate,
      deviceId: esp32.deviceId,
      wsConnected,
      esp32Connected: esp32.isConnected,
      reconnectAttempts,
      connectionFailures,
      shouldSuggestDemo: shouldSuggestDemo && autoSuggestDemo,
      diagnosticInfo
    };
  }, [
    calculateConnectionQuality,
    esp32.isConnected,
    esp32.deviceId,
    esp32.lastDataTimestamp,
    wsConnected,
    wsLastDataTime,
    reconnectAttempts,
    connectionFailures,
    shouldSuggestDemo,
    autoSuggestDemo,
    diagnosticInfo
  ]);

  /**
   * Handle connection timeout detection
   */
  const checkConnectionTimeout = useCallback(() => {
    const now = new Date();
    const lastUpdate = esp32.lastDataTimestamp || wsLastDataTime;
    
    if (lastUpdate) {
      const timeSinceLastData = now - new Date(lastUpdate);
      
      if (timeSinceLastData > timeoutThreshold && (esp32.isConnected || wsConnected)) {
        // Connection timeout detected
        console.warn('Connection timeout detected:', {
          timeSinceLastData,
          timeoutThreshold,
          esp32Connected: esp32.isConnected,
          wsConnected
        });

        // Update diagnostic info
        setDiagnosticInfo({
          type: 'timeout',
          message: `No data received for ${Math.floor(timeSinceLastData / 1000)} seconds`,
          timestamp: now,
          details: {
            lastDataTime: lastUpdate,
            esp32Connected: esp32.isConnected,
            wsConnected,
            deviceId: esp32.deviceId
          }
        });

        // Update ESP32 connection status if needed
        if (esp32.isConnected) {
          actions.setESP32Connection({
            isConnected: false,
            deviceId: null
          });
        }

        // Track failure
        handleConnectionFailure('timeout');
      }
    }
  }, [
    esp32.isConnected,
    esp32.lastDataTimestamp,
    esp32.deviceId,
    wsConnected,
    wsLastDataTime,
    timeoutThreshold,
    actions
  ]);

  /**
   * Handle connection failure tracking
   */
  const handleConnectionFailure = useCallback((reason = 'unknown') => {
    const now = new Date();
    
    // Only count as new failure if enough time has passed since last failure
    if (!lastFailureTime || (now - lastFailureTime) > 60000) {
      const newFailureCount = connectionFailures + 1;
      setConnectionFailures(newFailureCount);
      setLastFailureTime(now);

      console.log('Connection failure tracked:', {
        reason,
        failureCount: newFailureCount,
        timestamp: now
      });

      // Update diagnostic info
      setDiagnosticInfo({
        type: 'failure',
        message: `Connection failure: ${reason}`,
        timestamp: now,
        details: {
          reason,
          failureCount: newFailureCount,
          esp32Connected: esp32.isConnected,
          wsConnected,
          deviceId: esp32.deviceId
        }
      });

      // Suggest demo mode after threshold reached
      if (newFailureCount >= failureThreshold && !demo.isActive) {
        setShouldSuggestDemo(true);
        actions.addNotification(
          `Multiple connection failures detected. Consider switching to demo mode.`,
          'warning'
        );
      }
    }
  }, [
    connectionFailures,
    lastFailureTime,
    failureThreshold,
    demo.isActive,
    esp32.isConnected,
    esp32.deviceId,
    wsConnected,
    actions
  ]);

  /**
   * Handle successful connection recovery
   */
  const handleConnectionRecovery = useCallback(() => {
    console.log('Connection recovery detected');
    
    // Reset failure tracking
    setConnectionFailures(0);
    setLastFailureTime(null);
    setShouldSuggestDemo(false);
    
    // Clear diagnostic info
    setDiagnosticInfo(null);
    
    // Add success notification
    actions.addNotification('Connection restored successfully', 'success');
  }, [actions]);

  /**
   * Periodic connection quality assessment
   */
  const assessConnectionQuality = useCallback(() => {
    const quality = calculateConnectionQuality();
    const previousQuality = connectionQuality;
    
    if (quality !== previousQuality) {
      setConnectionQuality(quality);
      
      // Update ESP32 status with new quality
      actions.updateESP32Status({
        connectionQuality: quality
      });

      console.log('Connection quality changed:', {
        from: previousQuality,
        to: quality,
        timestamp: new Date()
      });
    }

    // Check for timeout
    checkConnectionTimeout();
  }, [calculateConnectionQuality, connectionQuality, checkConnectionTimeout, actions]);

  /**
   * Force connection retry
   */
  const retryConnection = useCallback(async () => {
    try {
      console.log('Attempting connection retry...');
      
      // Clear previous diagnostic info
      setDiagnosticInfo(null);
      
      // Add retry notification
      actions.addNotification('Retrying connection...', 'info');
      
      // This would typically trigger WebSocket reconnection
      // The actual retry logic is handled by the WebSocket service
      
      return true;
    } catch (error) {
      console.error('Connection retry failed:', error);
      
      setDiagnosticInfo({
        type: 'retry_failed',
        message: `Retry failed: ${error.message}`,
        timestamp: new Date(),
        details: { error: error.message }
      });
      
      handleConnectionFailure('retry_failed');
      return false;
    }
  }, [actions, handleConnectionFailure]);

  /**
   * Suggest demo mode activation
   */
  const suggestDemoMode = useCallback(() => {
    setShouldSuggestDemo(true);
    actions.addNotification(
      'Consider switching to demo mode for uninterrupted presentation',
      'info'
    );
  }, [actions]);

  /**
   * Dismiss demo mode suggestion
   */
  const dismissDemoSuggestion = useCallback(() => {
    setShouldSuggestDemo(false);
  }, []);

  // Set up periodic quality assessment
  useEffect(() => {
    qualityCheckRef.current = setInterval(assessConnectionQuality, qualityCheckInterval);
    
    return () => {
      if (qualityCheckRef.current) {
        clearInterval(qualityCheckRef.current);
      }
    };
  }, [assessConnectionQuality, qualityCheckInterval]);

  // Monitor connection state changes
  useEffect(() => {
    const deviceConnected = esp32.isConnected || wsConnected;
    const wasConnected = connectionQuality !== 'disconnected';
    
    if (deviceConnected && !wasConnected) {
      // Connection recovered
      handleConnectionRecovery();
    } else if (!deviceConnected && wasConnected) {
      // Connection lost
      handleConnectionFailure('disconnected');
    }
  }, [esp32.isConnected, wsConnected, connectionQuality, handleConnectionRecovery, handleConnectionFailure]);

  // Clean up timeouts on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (qualityCheckRef.current) {
        clearInterval(qualityCheckRef.current);
      }
    };
  }, []);

  return {
    // Connection status
    ...getConnectionStatus(),
    
    // Quality metrics
    connectionQuality,
    
    // Failure tracking
    connectionFailures,
    lastFailureTime,
    
    // Demo mode suggestion
    shouldSuggestDemo: shouldSuggestDemo && autoSuggestDemo,
    
    // Diagnostic information
    diagnosticInfo,
    
    // Control methods
    retryConnection,
    suggestDemoMode,
    dismissDemoSuggestion,
    handleConnectionFailure,
    handleConnectionRecovery,
    
    // Utility methods
    calculateConnectionQuality,
    checkConnectionTimeout
  };
};

export default useConnectionStatus;