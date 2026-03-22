/**
 * useWebSocket Hook for ESP32 Sensor Data Integration
 * 
 * React hook that provides WebSocket connection management and real-time data handling.
 * Integrates with AppContext for state management and provides connection status indicators.
 * 
 * Requirements implemented:
 * - 4.1: Establish WebSocket connection to FastAPI backend on component mount
 * - 4.5: Implement automatic reconnection every 5 seconds on connection failure
 * - 7.1: Add connection status indicators (green for connected, red for disconnected)
 */

import React, { useEffect, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import websocketService from '../services/websocketService';

/**
 * Custom hook for WebSocket connection management
 * @param {object} options - Configuration options
 * @param {boolean} options.autoConnect - Automatically connect on mount (default: true)
 * @param {string} options.url - WebSocket URL (default: ws://localhost:8000/ws/sensor-stream)
 * @param {function} options.onSensorData - Custom sensor data handler
 * @param {function} options.onDeviceStatus - Custom device status handler
 * @param {function} options.onError - Custom error handler
 * @returns {object} WebSocket connection state and methods
 */
export const useWebSocket = (options = {}) => {
  const { state, actions } = useApp();
  const {
    autoConnect = true,
    url = 'ws://localhost:8000/ws/sensor-stream',
    onSensorData,
    onDeviceStatus,
    onError
  } = options;

  // Use refs to avoid stale closures in event handlers
  const onSensorDataRef = useRef(onSensorData);
  const onDeviceStatusRef = useRef(onDeviceStatus);
  const onErrorRef = useRef(onError);

  // Update refs when handlers change
  useEffect(() => {
    onSensorDataRef.current = onSensorData;
    onDeviceStatusRef.current = onDeviceStatus;
    onErrorRef.current = onError;
  }, [onSensorData, onDeviceStatus, onError]);

  /**
   * Handle connection status changes
   */
  const handleConnectionChange = useCallback((status, info) => {
    console.log('WebSocket connection status changed:', status, info);

    // Update device connection status in AppContext
    const isConnected = status === 'connected';
    actions.setDeviceConnection({
      isConnected,
      deviceId: isConnected ? 'websocket-client' : null
    });

    // Add notification for connection changes
    if (status === 'connected') {
      actions.addNotification('WebSocket connected successfully', 'success');
    } else if (status === 'error') {
      actions.addError('WebSocket connection failed', 'error');
    } else if (status === 'disconnected' && info.reconnectAttempts > 0) {
      actions.addNotification(`WebSocket disconnected. Reconnecting... (attempt ${info.reconnectAttempts})`, 'warning');
    }
  }, [actions]);

  /**
   * Handle incoming sensor data with optimized real-time processing
   */
  const handleSensorData = useCallback((data) => {
    // Optimized processing - minimal logging and direct state updates
    
    // Process sensor data immediately for sub-50ms updates
    if (data.p !== undefined) { // Using shortened keys from optimized backend
      const postureUpdate = {
        tiltAngle: data.ta || 0,
        tiltDirection: data.td || 'center',
        fsrLeft: data.fl || 0,
        fsrRight: data.fr || 0,
        balance: data.b || 0,
        alertLevel: data.al || 'normal',
        hapticActive: data.al !== 'normal'
      };

      actions.updateLivePosture(postureUpdate);
    } else if (data.processed_data) {
      // Fallback for full format
      const postureUpdate = {
        tiltAngle: data.processed_data.tilt_angle || 0,
        tiltDirection: data.processed_data.tilt_direction || 'center',
        fsrLeft: data.raw_data?.fsr_left || 0,
        fsrRight: data.raw_data?.fsr_right || 0,
        balance: data.processed_data.fsr_balance || 0,
        alertLevel: data.processed_data.alert_level || 'normal',
        hapticActive: data.processed_data.alert_level !== 'normal'
      };

      actions.updateLivePosture(postureUpdate);
    }

    // Handle clinical data if present
    if (data.pd !== undefined || data.clinical_analysis) {
      const pusherDetected = data.pd || data.clinical_analysis?.pusher_detected || false;
      
      if (pusherDetected) {
        actions.setAlertLevel('unsafe');
        // Throttled notifications to avoid spam
        const now = Date.now();
        if (!handleSensorData.lastNotification || now - handleSensorData.lastNotification > 5000) {
          actions.addNotification('Pusher syndrome detected', 'warning');
          handleSensorData.lastNotification = now;
        }
      }
    }

    // Call custom handler if provided
    if (onSensorDataRef.current) {
      onSensorDataRef.current(data);
    }
  }, [actions]);

  // Add throttling property to function
  handleSensorData.lastNotification = 0;

  /**
   * Handle device status updates with minimal overhead
   */
  const handleDeviceStatus = useCallback((deviceId, status) => {
    // Optimized device status handling
    const isConnected = status.connection_status === 'connected' || status.connected_devices > 0;
    
    actions.setDeviceConnection({
      isConnected,
      deviceId: deviceId
    });

    // Throttled notifications for status changes
    const now = Date.now();
    if (!handleDeviceStatus.lastNotification || now - handleDeviceStatus.lastNotification > 3000) {
      if (isConnected && !handleDeviceStatus.wasConnected) {
        actions.addNotification('ESP32 device connected', 'success');
        handleDeviceStatus.lastNotification = now;
      } else if (!isConnected && handleDeviceStatus.wasConnected) {
        actions.addNotification('ESP32 device disconnected', 'warning');
        handleDeviceStatus.lastNotification = now;
      }
    }
    
    handleDeviceStatus.wasConnected = isConnected;

    // Call custom handler if provided
    if (onDeviceStatusRef.current) {
      onDeviceStatusRef.current(deviceId, status);
    }
  }, [actions]);

  // Add throttling properties to function
  handleDeviceStatus.lastNotification = 0;
  handleDeviceStatus.wasConnected = false;

  /**
   * Handle WebSocket errors
   */
  const handleError = useCallback((error) => {
    console.error('WebSocket error:', error);
    actions.addError(`WebSocket error: ${error}`, 'error');

    // Call custom error handler if provided
    if (onErrorRef.current) {
      onErrorRef.current(error);
    }
  }, [actions]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    websocketService.connect(url);
  }, [url]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  /**
   * Send message to WebSocket server
   */
  const sendMessage = useCallback((message) => {
    return websocketService.sendMessage(message);
  }, []);

  /**
   * Request device status from server
   */
  const requestDeviceStatus = useCallback(() => {
    return websocketService.requestDeviceStatus();
  }, []);

  /**
   * Get connection information
   */
  const getConnectionInfo = useCallback(() => {
    return websocketService.getConnectionInfo();
  }, []);

  // Set up event listeners on mount
  useEffect(() => {
    websocketService.setEventListeners({
      onConnectionChange: handleConnectionChange,
      onSensorData: handleSensorData,
      onDeviceStatus: handleDeviceStatus,
      onError: handleError
    });

    // Auto-connect if enabled
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (autoConnect) {
        disconnect();
      }
      websocketService.setEventListeners({
        onConnectionChange: null,
        onSensorData: null,
        onDeviceStatus: null,
        onError: null
      });
    };
  }, [autoConnect, connect, disconnect, handleConnectionChange, handleSensorData, handleDeviceStatus, handleError]);

  // Get current connection status from service
  const connectionInfo = websocketService.getConnectionInfo() || {
    status: 'disconnected',
    isConnected: false,
    reconnectAttempts: 0,
    lastConnectionTime: null,
    lastDataTime: null,
    readyState: 3 // WebSocket.CLOSED
  };

  return {
    // Connection state
    isConnected: connectionInfo.isConnected,
    connectionStatus: connectionInfo.status,
    reconnectAttempts: connectionInfo.reconnectAttempts,
    lastConnectionTime: connectionInfo.lastConnectionTime,
    lastDataTime: connectionInfo.lastDataTime,

    // Connection methods
    connect,
    disconnect,
    sendMessage,
    requestDeviceStatus,
    getConnectionInfo,

    // Convenience methods
    isConnecting: connectionInfo.status === 'connecting',
    hasError: connectionInfo.status === 'error',
    
    // Connection quality indicator
    connectionQuality: connectionInfo.isConnected ? 
      (connectionInfo.lastDataTime && (Date.now() - connectionInfo.lastDataTime.getTime()) < 5000 ? 'excellent' : 'good') : 
      'poor'
  };
};

export default useWebSocket;