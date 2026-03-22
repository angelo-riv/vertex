/**
 * WebSocket Connection Status Indicator
 * 
 * Displays real-time WebSocket connection status with color-coded indicators.
 * Shows connection quality, reconnection attempts, and last data timestamp.
 * 
 * Requirements implemented:
 * - 4.5: Display connection status indicators and attempt reconnection every 5 seconds
 * - 4.6: Show green connection indicator with ESP32 device status and data freshness
 * - 7.4: Show "Device Disconnected" message with last update time
 */

import React from 'react';
import { useApp } from '../../context/AppContext';
import useWebSocket from '../../hooks/useWebSocket';

const WebSocketStatus = ({ 
  showDetails = false, 
  className = '',
  size = 'medium' // 'small', 'medium', 'large'
}) => {
  const { state } = useApp();
  const { 
    isConnected, 
    connectionStatus, 
    reconnectAttempts, 
    lastConnectionTime, 
    lastDataTime,
    connectionQuality 
  } = useWebSocket({ autoConnect: false }); // Don't auto-connect here, let parent handle it

  // Determine status color and icon
  const getStatusInfo = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          color: '#10b981', // green-500
          bgColor: '#d1fae5', // green-100
          icon: '●',
          text: 'Connected',
          description: 'Real-time data streaming active'
        };
      case 'connecting':
        return {
          color: '#f59e0b', // amber-500
          bgColor: '#fef3c7', // amber-100
          icon: '◐',
          text: 'Connecting...',
          description: 'Establishing WebSocket connection'
        };
      case 'disconnected':
        return {
          color: '#ef4444', // red-500
          bgColor: '#fee2e2', // red-100
          icon: '●',
          text: 'Disconnected',
          description: reconnectAttempts > 0 ? `Reconnecting... (attempt ${reconnectAttempts})` : 'Connection lost'
        };
      case 'error':
        return {
          color: '#dc2626', // red-600
          bgColor: '#fecaca', // red-200
          icon: '⚠',
          text: 'Error',
          description: 'Connection failed'
        };
      default:
        return {
          color: '#6b7280', // gray-500
          bgColor: '#f3f4f6', // gray-100
          icon: '○',
          text: 'Unknown',
          description: 'Status unknown'
        };
    }
  };

  const statusInfo = getStatusInfo();

  // Format time display
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Never';
    const now = new Date();
    const diff = Math.floor((now - timestamp) / 1000);
    
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return timestamp.toLocaleTimeString();
  };

  // Get connection quality indicator
  const getQualityIndicator = () => {
    switch (connectionQuality) {
      case 'excellent':
        return { color: '#10b981', bars: 3, text: 'Excellent' };
      case 'good':
        return { color: '#f59e0b', bars: 2, text: 'Good' };
      case 'poor':
        return { color: '#ef4444', bars: 1, text: 'Poor' };
      default:
        return { color: '#6b7280', bars: 0, text: 'Unknown' };
    }
  };

  const qualityInfo = getQualityIndicator();

  // Size-based styling
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          container: 'px-2 py-1 text-xs',
          icon: 'text-xs',
          text: 'text-xs',
          details: 'text-xs'
        };
      case 'large':
        return {
          container: 'px-4 py-3 text-base',
          icon: 'text-lg',
          text: 'text-base font-medium',
          details: 'text-sm'
        };
      default: // medium
        return {
          container: 'px-3 py-2 text-sm',
          icon: 'text-sm',
          text: 'text-sm font-medium',
          details: 'text-xs'
        };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <div 
      className={`inline-flex items-center rounded-lg border ${sizeStyles.container} ${className}`}
      style={{ 
        backgroundColor: statusInfo.bgColor,
        borderColor: statusInfo.color,
        color: statusInfo.color
      }}
    >
      {/* Status Icon */}
      <span 
        className={`${sizeStyles.icon} mr-2`}
        style={{ color: statusInfo.color }}
        title={statusInfo.description}
      >
        {statusInfo.icon}
      </span>

      {/* Status Text */}
      <span className={sizeStyles.text}>
        {statusInfo.text}
      </span>

      {/* Connection Quality Bars (for connected state) */}
      {isConnected && (
        <div className="ml-2 flex items-center space-x-1">
          {[1, 2, 3].map((bar) => (
            <div
              key={bar}
              className="w-1 h-3 rounded-sm"
              style={{
                backgroundColor: bar <= qualityInfo.bars ? qualityInfo.color : '#e5e7eb'
              }}
            />
          ))}
        </div>
      )}

      {/* Detailed Information */}
      {showDetails && (
        <div className="ml-3 flex flex-col">
          <div className={`${sizeStyles.details} text-gray-600`}>
            {statusInfo.description}
          </div>
          
          {lastConnectionTime && (
            <div className={`${sizeStyles.details} text-gray-500`}>
              Connected: {formatTime(lastConnectionTime)}
            </div>
          )}
          
          {lastDataTime && (
            <div className={`${sizeStyles.details} text-gray-500`}>
              Last data: {formatTime(lastDataTime)}
            </div>
          )}
          
          {state.esp32.deviceId && (
            <div className={`${sizeStyles.details} text-gray-500`}>
              Device: {state.esp32.deviceId}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WebSocketStatus;