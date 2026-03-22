/**
 * WebSocket Provider Component
 * 
 * Provides WebSocket connection management at the application level.
 * Automatically establishes connection and handles reconnection logic.
 * Integrates with AppContext for state management.
 * 
 * Requirements implemented:
 * - 4.1: Establish WebSocket connection to FastAPI backend on component mount
 * - 4.5: Implement automatic reconnection every 5 seconds on connection failure
 * - 7.1: Add connection status indicators and real-time updates
 */

import React, { useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import useWebSocket from '../../hooks/useWebSocket';

const WebSocketProvider = ({ children, url = 'ws://localhost:8000/ws/sensor-stream' }) => {
  const { state, actions } = useApp();

  // Custom handlers for WebSocket events
  const handleSensorData = useCallback((data) => {
    console.log('WebSocketProvider: Processing sensor data', data);

    // Update ESP32 connection status
    if (data.device_id) {
      actions.setESP32Connection({
        isConnected: true,
        deviceId: data.device_id
      });

      actions.updateESP32Status({
        lastDataTimestamp: new Date(),
        connectionQuality: 'excellent'
      });
    }

    // Process clinical analysis data
    if (data.clinical_analysis) {
      const { pusher_detected, severity_score, confidence_level } = data.clinical_analysis;
      
      if (pusher_detected !== undefined) {
        actions.setPusherDetected(pusher_detected, severity_score);
      }

      if (severity_score !== undefined) {
        actions.updateClinicalScore(severity_score);
      }

      // Add episode if pusher syndrome is detected
      if (pusher_detected && severity_score > 0) {
        const episode = {
          id: Date.now(),
          timestamp: new Date(),
          severity: severity_score,
          confidence: confidence_level,
          tiltAngle: data.processed_data?.tilt_angle || 0,
          isActive: true
        };
        actions.addEpisode(episode);
      }
    }
  }, [actions]);

  const handleDeviceStatus = useCallback((deviceId, status) => {
    console.log('WebSocketProvider: Processing device status', deviceId, status);

    // Update ESP32 connection based on device status
    const isConnected = status.connection_status === 'connected';
    
    actions.setESP32Connection({
      isConnected,
      deviceId: isConnected ? deviceId : null
    });

    // Update connection quality based on status
    let connectionQuality = 'disconnected';
    if (status.connection_status === 'connected') {
      const secondsAgo = status.last_seen_seconds_ago || 0;
      if (secondsAgo < 2) {
        connectionQuality = 'excellent';
      } else if (secondsAgo < 5) {
        connectionQuality = 'good';
      } else {
        connectionQuality = 'poor';
      }
    }

    actions.updateESP32Status({
      connectionQuality,
      lastDataTimestamp: status.last_seen ? new Date(status.last_seen) : null
    });
  }, [actions]);

  const handleError = useCallback((error) => {
    console.error('WebSocketProvider: WebSocket error', error);
    
    // Update ESP32 connection status on error
    actions.setESP32Connection({
      isConnected: false,
      deviceId: null
    });

    actions.updateESP32Status({
      connectionQuality: 'disconnected'
    });
  }, [actions]);

  // Initialize WebSocket connection
  const {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    requestDeviceStatus
  } = useWebSocket({
    autoConnect: true,
    url,
    onSensorData: handleSensorData,
    onDeviceStatus: handleDeviceStatus,
    onError: handleError
  });

  // Request initial device status when connected
  useEffect(() => {
    if (isConnected) {
      // Wait a moment for connection to stabilize, then request device status
      const timer = setTimeout(() => {
        requestDeviceStatus();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [isConnected, requestDeviceStatus]);

  // Periodic device status requests to keep data fresh
  useEffect(() => {
    if (isConnected) {
      const interval = setInterval(() => {
        requestDeviceStatus();
      }, 30000); // Request every 30 seconds

      return () => clearInterval(interval);
    }
  }, [isConnected, requestDeviceStatus]);

  // Handle demo mode changes
  useEffect(() => {
    if (state.demo.isActive !== state.esp32.demoMode) {
      actions.setESP32DemoMode(state.demo.isActive);
    }
  }, [state.demo.isActive, state.esp32.demoMode, actions]);

  // Provide WebSocket methods to child components via context if needed
  const webSocketContext = {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    requestDeviceStatus
  };

  // Add WebSocket context to window for debugging (development only)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      window.webSocketDebug = webSocketContext;
    }
  }, [webSocketContext]);

  return (
    <>
      {children}
    </>
  );
};

export default WebSocketProvider;