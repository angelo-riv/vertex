/**
 * WebSocket Demo Component
 * 
 * Demonstrates WebSocket connection functionality with real-time status updates,
 * connection controls, and message testing capabilities.
 */

import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import useWebSocket from '../../hooks/useWebSocket';
import WebSocketStatus from '../monitoring/WebSocketStatus';

const WebSocketDemo = () => {
  const { state } = useApp();
  const [testMessage, setTestMessage] = useState('');
  const [receivedMessages, setReceivedMessages] = useState([]);

  // Custom handlers for demo
  const handleSensorData = (data) => {
    console.log('Demo: Received sensor data', data);
    setReceivedMessages(prev => [
      { type: 'sensor_data', timestamp: new Date(), data },
      ...prev.slice(0, 9) // Keep last 10 messages
    ]);
  };

  const handleDeviceStatus = (deviceId, status) => {
    console.log('Demo: Received device status', deviceId, status);
    setReceivedMessages(prev => [
      { type: 'device_status', timestamp: new Date(), data: { deviceId, status } },
      ...prev.slice(0, 9)
    ]);
  };

  const handleError = (error) => {
    console.log('Demo: WebSocket error', error);
    setReceivedMessages(prev => [
      { type: 'error', timestamp: new Date(), data: { error } },
      ...prev.slice(0, 9)
    ]);
  };

  const {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    sendMessage,
    requestDeviceStatus,
    getConnectionInfo
  } = useWebSocket({
    autoConnect: false, // Manual control for demo
    onSensorData: handleSensorData,
    onDeviceStatus: handleDeviceStatus,
    onError: handleError
  });

  const handleSendTestMessage = () => {
    if (testMessage.trim()) {
      const success = sendMessage({
        type: 'test_message',
        message: testMessage,
        timestamp: new Date().toISOString()
      });
      
      if (success) {
        setReceivedMessages(prev => [
          { type: 'sent', timestamp: new Date(), data: { message: testMessage } },
          ...prev.slice(0, 9)
        ]);
        setTestMessage('');
      }
    }
  };

  const connectionInfo = getConnectionInfo();

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <h2 style={{
        fontSize: 'var(--font-size-xl)',
        fontWeight: '600',
        color: 'var(--primary-blue)',
        marginBottom: 'var(--spacing-4)'
      }}>
        WebSocket Connection Demo
      </h2>

      {/* Connection Status */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-3)'
        }}>
          Connection Status
        </h3>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-3)'
        }}>
          <WebSocketStatus showDetails={true} size="medium" />
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--spacing-2)',
          fontSize: 'var(--font-size-sm)',
          color: 'var(--gray-600)'
        }}>
          <div>Status: <strong>{connectionStatus}</strong></div>
          <div>Connected: <strong>{isConnected ? 'Yes' : 'No'}</strong></div>
          <div>Reconnect Attempts: <strong>{connectionInfo.reconnectAttempts}</strong></div>
          <div>Ready State: <strong>{connectionInfo.readyState}</strong></div>
        </div>
      </div>

      {/* Connection Controls */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-3)'
        }}>
          Connection Controls
        </h3>
        
        <div style={{
          display: 'flex',
          gap: 'var(--spacing-2)',
          flexWrap: 'wrap'
        }}>
          <button
            onClick={connect}
            disabled={isConnected}
            style={{
              backgroundColor: isConnected ? 'var(--gray-300)' : 'var(--primary-blue)',
              color: isConnected ? 'var(--gray-500)' : 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-3)',
              fontSize: 'var(--font-size-sm)',
              cursor: isConnected ? 'not-allowed' : 'pointer',
              transition: 'var(--transition-fast)'
            }}
          >
            Connect
          </button>
          
          <button
            onClick={disconnect}
            disabled={!isConnected}
            style={{
              backgroundColor: !isConnected ? 'var(--gray-300)' : 'var(--red-500)',
              color: !isConnected ? 'var(--gray-500)' : 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-3)',
              fontSize: 'var(--font-size-sm)',
              cursor: !isConnected ? 'not-allowed' : 'pointer',
              transition: 'var(--transition-fast)'
            }}
          >
            Disconnect
          </button>
          
          <button
            onClick={requestDeviceStatus}
            disabled={!isConnected}
            style={{
              backgroundColor: !isConnected ? 'var(--gray-300)' : 'var(--green-500)',
              color: !isConnected ? 'var(--gray-500)' : 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-3)',
              fontSize: 'var(--font-size-sm)',
              cursor: !isConnected ? 'not-allowed' : 'pointer',
              transition: 'var(--transition-fast)'
            }}
          >
            Request Device Status
          </button>
        </div>
      </div>

      {/* Message Testing */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-3)'
        }}>
          Send Test Message
        </h3>
        
        <div style={{
          display: 'flex',
          gap: 'var(--spacing-2)'
        }}>
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter test message..."
            disabled={!isConnected}
            style={{
              flex: 1,
              padding: 'var(--spacing-2)',
              border: '1px solid var(--gray-300)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              backgroundColor: !isConnected ? 'var(--gray-100)' : 'white'
            }}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSendTestMessage();
              }
            }}
          />
          
          <button
            onClick={handleSendTestMessage}
            disabled={!isConnected || !testMessage.trim()}
            style={{
              backgroundColor: (!isConnected || !testMessage.trim()) ? 'var(--gray-300)' : 'var(--primary-blue)',
              color: (!isConnected || !testMessage.trim()) ? 'var(--gray-500)' : 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-3)',
              fontSize: 'var(--font-size-sm)',
              cursor: (!isConnected || !testMessage.trim()) ? 'not-allowed' : 'pointer',
              transition: 'var(--transition-fast)'
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* App State Display */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-3)'
        }}>
          App State (ESP32 & Clinical)
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: 'var(--spacing-3)',
          fontSize: 'var(--font-size-sm)'
        }}>
          <div>
            <strong>ESP32 Connection:</strong>
            <div>Connected: {state.esp32.isConnected ? 'Yes' : 'No'}</div>
            <div>Device ID: {state.esp32.deviceId || 'None'}</div>
            <div>Quality: {state.esp32.connectionQuality}</div>
            <div>Demo Mode: {state.esp32.demoMode ? 'Yes' : 'No'}</div>
          </div>
          
          <div>
            <strong>Clinical Data:</strong>
            <div>Pusher Detected: {state.clinical.pusherDetected ? 'Yes' : 'No'}</div>
            <div>Clinical Score: {state.clinical.clinicalScore}</div>
            <div>Episodes: {state.clinical.episodeHistory.length}</div>
          </div>
          
          <div>
            <strong>Live Posture:</strong>
            <div>Tilt Angle: {state.monitoring.livePosture.tiltAngle}°</div>
            <div>Direction: {state.monitoring.livePosture.tiltDirection}</div>
            <div>Alert Level: {state.monitoring.livePosture.alertLevel}</div>
          </div>
        </div>
      </div>

      {/* Recent Messages */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-4)',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          marginBottom: 'var(--spacing-3)'
        }}>
          Recent Messages ({receivedMessages.length})
        </h3>
        
        {receivedMessages.length === 0 ? (
          <div style={{
            color: 'var(--gray-500)',
            fontStyle: 'italic',
            textAlign: 'center',
            padding: 'var(--spacing-4)'
          }}>
            No messages received yet. Connect and send a test message or wait for sensor data.
          </div>
        ) : (
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            {receivedMessages.map((msg, index) => (
              <div
                key={index}
                style={{
                  padding: 'var(--spacing-2)',
                  marginBottom: 'var(--spacing-2)',
                  backgroundColor: msg.type === 'error' ? 'var(--red-50)' : 
                                  msg.type === 'sent' ? 'var(--blue-50)' : 'var(--gray-50)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--font-size-sm)'
                }}
              >
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: 'var(--spacing-1)'
                }}>
                  <span style={{
                    fontWeight: '600',
                    color: msg.type === 'error' ? 'var(--red-600)' : 
                           msg.type === 'sent' ? 'var(--blue-600)' : 'var(--gray-700)'
                  }}>
                    {msg.type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-xs)' }}>
                    {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <pre style={{
                  margin: 0,
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--gray-600)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {JSON.stringify(msg.data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WebSocketDemo;