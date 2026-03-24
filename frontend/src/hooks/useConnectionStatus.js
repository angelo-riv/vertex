/**
 * useConnectionStatus Hook
 *
 * Reads WebSocket + ESP32 connection state from AppContext and the
 * websocketService singleton. Does NOT touch the WebSocket connection itself.
 */

import { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import websocketService from '../services/websocketService';

export const useConnectionStatus = (options = {}) => {
  const { timeoutThreshold = 5000, autoSuggestDemo = true } = options;
  const { state, actions } = useApp();
  const { esp32 } = state;

  const [connectionInfo, setConnectionInfo] = useState(() => websocketService.getConnectionInfo());

  // Poll singleton — no listener registration
  useEffect(() => {
    const interval = setInterval(() => {
      setConnectionInfo(websocketService.getConnectionInfo());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const wsConnected = connectionInfo.isConnected;
  const wsStatus = connectionInfo.status;
  const wsLastDataTime = connectionInfo.lastDataTime;
  const reconnectAttempts = connectionInfo.reconnectAttempts;

  const calculateConnectionQuality = useCallback(() => {
    const lastUpdate = esp32.lastDataTimestamp || wsLastDataTime;
    if (!lastUpdate) return 'disconnected';
    const age = Date.now() - new Date(lastUpdate).getTime();
    const connected = esp32.isConnected || wsConnected;
    if (connected && age < 2000) return 'excellent';
    if (connected && age < 5000) return 'good';
    if (connected && age < 15000) return 'poor';
    return 'disconnected';
  }, [esp32.isConnected, esp32.lastDataTimestamp, wsConnected, wsLastDataTime]);

  const retryConnection = useCallback(() => {
    actions.addNotification('Retrying connection...', 'info');
  }, [actions]);

  const quality = calculateConnectionQuality();

  return {
    isConnected: esp32.isConnected || wsConnected,
    quality,
    connectionQuality: quality,
    wsConnected,
    esp32Connected: esp32.isConnected,
    reconnectAttempts,
    lastDataTime: esp32.lastDataTimestamp || wsLastDataTime,
    deviceId: esp32.deviceId,
    retryConnection,
    shouldSuggestDemo: false,
    diagnosticInfo: null,
    connectionFailures: 0,
  };
};

export default useConnectionStatus;
