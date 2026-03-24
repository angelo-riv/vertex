/**
 * useWebSocket Hook
 *
 * READ-ONLY hook — it reads state from the websocketService singleton but
 * does NOT connect, disconnect, or overwrite event listeners.
 * WebSocketProvider is the sole owner of the connection lifecycle.
 */

import { useState, useEffect } from 'react';
import websocketService from '../services/websocketService';

export const useWebSocket = (options = {}) => {
  const [connectionInfo, setConnectionInfo] = useState(() => websocketService.getConnectionInfo());

  // Poll the singleton every second — no listener registration, no connect/disconnect
  useEffect(() => {
    const interval = setInterval(() => {
      setConnectionInfo(websocketService.getConnectionInfo());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return {
    isConnected: connectionInfo.isConnected,
    connectionStatus: connectionInfo.status,
    reconnectAttempts: connectionInfo.reconnectAttempts,
    lastConnectionTime: connectionInfo.lastConnectionTime,
    lastDataTime: connectionInfo.lastDataTime,
    isConnecting: connectionInfo.status === 'connecting',
    hasError: connectionInfo.status === 'error',
  };
};

export default useWebSocket;
