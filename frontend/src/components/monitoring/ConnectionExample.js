/**
 * Connection Management Usage Example
 * 
 * Demonstrates how to integrate the connection management components
 * in different parts of the application for ESP32 device monitoring.
 * 
 * This example shows:
 * - Header status widget
 * - Full connection manager
 * - Fallback component integration
 * - Custom event handlers
 */

import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  ConnectionManager,
  ConnectionFallback,
  ConnectionStatusWidget,
  useConnectionStatus
} from './index';

const ConnectionExample = () => {
  const { state, actions } = useApp();
  const [showFullManager, setShowFullManager] = useState(false);
  
  // Custom connection status with additional logic
  const {
    isConnected,
    connectionQuality,
    shouldSuggestDemo,
    retryConnection,
    diagnosticInfo
  } = useConnectionStatus({
    timeoutThreshold: 5000,
    failureThreshold: 3,
    autoSuggestDemo: true
  });

  // Custom demo mode activation handler
  const handleDemoModeActivation = async () => {
    try {
      console.log('Activating demo mode due to connection issues...');
      
      // Call backend to enable demo mode
      const response = await fetch('http://localhost:8000/api/demo/toggle?enabled=true&device_id=ESP32_FALLBACK', {
        method: 'POST'
      });

      if (response.ok) {
        actions.startDemoMode('ESP32_FALLBACK', 'normal_posture');
        actions.addNotification('Demo mode activated for presentation', 'success');
      } else {
        throw new Error('Failed to activate demo mode');
      }
    } catch (error) {
      console.error('Demo mode activation failed:', error);
      actions.addError('Failed to activate demo mode', 'error');
    }
  };

  // Custom connection retry handler
  const handleConnectionRetry = async () => {
    try {
      console.log('Attempting manual connection retry...');
      
      // Clear any existing errors
      actions.removeError();
      
      // Attempt to reconnect
      await retryConnection();
      
      // Add success notification
      actions.addNotification('Connection retry initiated', 'info');
    } catch (error) {
      console.error('Connection retry failed:', error);
      actions.addError('Connection retry failed', 'error');
    }
  };

  return (
    <div style={{ padding: 'var(--spacing-4)' }}>
      <h2 style={{ marginBottom: 'var(--spacing-4)' }}>
        Connection Management Examples
      </h2>

      {/* Header Status Widget Example */}
      <section style={{ marginBottom: 'var(--spacing-6)' }}>
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>
          Header Status Widget
        </h3>
        <p style={{ 
          marginBottom: 'var(--spacing-3)', 
          color: 'var(--gray-600)',
          fontSize: 'var(--font-size-sm)'
        }}>
          Compact status display for headers, navigation bars, or status panels.
        </p>
        
        <div style={{
          display: 'flex',
          gap: 'var(--spacing-3)',
          alignItems: 'center',
          padding: 'var(--spacing-3)',
          backgroundColor: 'var(--gray-50)',
          borderRadius: 'var(--border-radius-md)',
          border: '1px solid var(--gray-200)'
        }}>
          <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: '500' }}>
            Status:
          </span>
          <ConnectionStatusWidget 
            size="small"
            showLabels={true}
            showInternetStatus={true}
            onClick={() => setShowFullManager(!showFullManager)}
          />
          <ConnectionStatusWidget 
            size="medium"
            showLabels={true}
            showInternetStatus={false}
          />
          <ConnectionStatusWidget 
            size="large"
            showLabels={true}
            showInternetStatus={true}
          />
        </div>
      </section>

      {/* Full Connection Manager Example */}
      <section style={{ marginBottom: 'var(--spacing-6)' }}>
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>
          Full Connection Manager
        </h3>
        <p style={{ 
          marginBottom: 'var(--spacing-3)', 
          color: 'var(--gray-600)',
          fontSize: 'var(--font-size-sm)'
        }}>
          Complete connection management with fallback suggestions and detailed status.
        </p>
        
        <button
          onClick={() => setShowFullManager(!showFullManager)}
          style={{
            marginBottom: 'var(--spacing-3)',
            padding: '8px 16px',
            backgroundColor: 'var(--primary-blue)',
            color: 'white',
            border: 'none',
            borderRadius: 'var(--border-radius-md)',
            cursor: 'pointer'
          }}
        >
          {showFullManager ? 'Hide' : 'Show'} Full Manager
        </button>

        {showFullManager && (
          <ConnectionManager
            onDemoModeActivate={handleDemoModeActivation}
            onRetryConnection={handleConnectionRetry}
            showDetails={true}
          />
        )}
      </section>

      {/* Connection Fallback Example */}
      <section style={{ marginBottom: 'var(--spacing-6)' }}>
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>
          Connection Fallback Component
        </h3>
        <p style={{ 
          marginBottom: 'var(--spacing-3)', 
          color: 'var(--gray-600)',
          fontSize: 'var(--font-size-sm)'
        }}>
          Focused fallback component for integration into existing displays.
        </p>
        
        <ConnectionFallback
          onDemoModeActivate={handleDemoModeActivation}
          onRetryConnection={handleConnectionRetry}
          showInternetStatus={true}
        />
      </section>

      {/* Connection Status Information */}
      <section style={{ marginBottom: 'var(--spacing-6)' }}>
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>
          Current Connection Status
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--spacing-3)',
          padding: 'var(--spacing-4)',
          backgroundColor: 'var(--gray-50)',
          borderRadius: 'var(--border-radius-lg)',
          border: '1px solid var(--gray-200)'
        }}>
          <div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Connection Status
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: isConnected ? '#10b981' : '#ef4444'
            }}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          <div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Connection Quality
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              textTransform: 'capitalize'
            }}>
              {connectionQuality}
            </div>
          </div>

          <div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Demo Suggestion
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: shouldSuggestDemo ? '#f59e0b' : '#10b981'
            }}>
              {shouldSuggestDemo ? 'Suggested' : 'Not needed'}
            </div>
          </div>

          <div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Demo Mode
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: state.demo.isActive ? '#8b5cf6' : 'var(--gray-600)'
            }}>
              {state.demo.isActive ? 'Active' : 'Inactive'}
            </div>
          </div>
        </div>

        {/* Diagnostic Information */}
        {diagnosticInfo && (
          <div style={{
            marginTop: 'var(--spacing-3)',
            padding: 'var(--spacing-3)',
            backgroundColor: '#fef3c7',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid #fcd34d'
          }}>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              color: '#92400e',
              marginBottom: 'var(--spacing-1)'
            }}>
              Diagnostic Information
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: '#a16207',
              fontFamily: 'monospace'
            }}>
              {diagnosticInfo.message}
            </div>
          </div>
        )}
      </section>

      {/* Integration Notes */}
      <section>
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>
          Integration Notes
        </h3>
        
        <div style={{
          padding: 'var(--spacing-4)',
          backgroundColor: '#f0f9ff',
          borderRadius: 'var(--border-radius-lg)',
          border: '1px solid #bae6fd'
        }}>
          <ul style={{
            margin: 0,
            paddingLeft: 'var(--spacing-4)',
            fontSize: 'var(--font-size-sm)',
            color: '#0369a1',
            lineHeight: 1.6
          }}>
            <li>Use <code>ConnectionStatusWidget</code> in headers and navigation bars</li>
            <li>Use <code>ConnectionManager</code> for dedicated connection status pages</li>
            <li>Use <code>ConnectionFallback</code> to integrate into existing sensor displays</li>
            <li>All components automatically handle ESP32 and internet connectivity separately</li>
            <li>Demo mode suggestions appear after 3 connection failures by default</li>
            <li>Internet connectivity is checked independently every 30 seconds</li>
            <li>Connection quality is assessed based on data freshness and WebSocket status</li>
          </ul>
        </div>
      </section>
    </div>
  );
};

export default ConnectionExample;