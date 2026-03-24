import React, { useState, useEffect } from 'react';
import PostureVisualization from '../components/monitoring/PostureVisualization';
import CircularTiltMeter from '../components/monitoring/CircularTiltMeter';
import SensorDataDisplay from '../components/monitoring/SensorDataDisplay';
import AlertMessage from '../components/monitoring/AlertMessage';
import { useApp } from '../context/AppContext';

const SessionPage = () => {
  const { state, actions } = useApp();
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [alertVisible, setAlertVisible] = useState(false);

  // Read connection status from AppContext (managed by WebSocketProvider)
  const wsConnected = state.esp32.isConnected;

  // Extract real-time data from AppContext (updated by WebSocket)
  const {
    monitoring: { livePosture, alertLevel },
    esp32: { isConnected: esp32Connected, deviceId, connectionQuality, demoMode },
    clinical: { pusherDetected, clinicalScore, thresholds },
    calibration: { status: calibrationStatus, baseline, progress, lastCalibrationDate }
  } = state;

  // Session timer effect
  useEffect(() => {
    let interval = null;
    if (isSessionActive) {
      interval = setInterval(() => {
        setSessionDuration(duration => duration + 1);
      }, 1000);
    } else if (!isSessionActive && sessionDuration !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isSessionActive, sessionDuration]);

  // Auto-show alerts for pusher detection
  useEffect(() => {
    if (pusherDetected && !alertVisible) {
      setAlertVisible(true);
    }
  }, [pusherDetected, alertVisible]);

  // Real-time sensor data (from WebSocket updates via AppContext)
  const realTimeSensorData = {
    imu: { 
      pitch: livePosture.tiltAngle || 0, 
      roll: 0, // Roll not currently used in posture monitoring
      yaw: 0   // Yaw not currently used in posture monitoring
    },
    fsr: { 
      left: livePosture.fsrLeft || 0, 
      right: livePosture.fsrRight || 0 
    },
    isConnected: esp32Connected || wsConnected,
    hapticActive: livePosture.hapticActive || false,
    alertLevel: alertLevel || 'safe'
  };

  // ESP32 status for enhanced monitoring
  const esp32Status = {
    isConnected: esp32Connected,
    deviceId: deviceId,
    lastDataTimestamp: livePosture.timestamp,
    connectionQuality: connectionQuality,
    demoMode: demoMode
  };

  // Clinical data for enhanced analytics
  const clinicalData = {
    pusherDetected: pusherDetected,
    currentEpisode: state.clinical.currentEpisode,
    clinicalScore: clinicalScore,
    confidence: 0.8, // TODO: Get from actual clinical analysis
    episodeCount: state.clinical.episodeHistory.length
  };

  // Calibration status for device management
  const calibrationData = {
    status: calibrationStatus,
    progress: progress,
    baseline: baseline,
    lastCalibrationDate: lastCalibrationDate
  };

  const handleStartSession = () => {
    setIsSessionActive(true);
    actions.startMonitoring(`session-${Date.now()}`);
  };

  const handleStopSession = () => {
    setIsSessionActive(false);
    setSessionDuration(0);
    actions.stopMonitoring();
  };

  const handleStartCalibration = () => {
    // TODO: Implement calibration start logic
    console.log('Starting calibration...');
    actions.updateCalibrationProgress(0);
  };

  const handleToggleDemoMode = () => {
    const newDemoMode = !demoMode;
    actions.setESP32DemoMode(newDemoMode);
    if (newDemoMode) {
      actions.startDemoMode('demo-device', 'normal_posture');
    } else {
      actions.stopDemoMode();
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '1200px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 160px)'
    }}>
      {/* Session Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--spacing-4)'
        }}>
          <div>
            <h2 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: '700',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)',
              letterSpacing: '-0.025em'
            }}>
              Rehabilitation Session
            </h2>
            <p style={{
              fontSize: 'var(--font-size-lg)',
              color: 'var(--gray-600)',
              margin: 0
            }}>
              Monitor your posture and receive real-time feedback
            </p>
          </div>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-3)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: '700',
              color: isSessionActive ? 'var(--success-green)' : 'var(--gray-500)',
              fontFamily: 'monospace'
            }}>
              {formatTime(sessionDuration)}
            </div>
            <button
              className={`btn ${isSessionActive ? 'btn-danger' : 'btn-primary'}`}
              onClick={isSessionActive ? handleStopSession : handleStartSession}
              style={{
                padding: 'var(--spacing-3) var(--spacing-6)',
                fontSize: 'var(--font-size-base)',
                fontWeight: '600',
                minWidth: '120px',
                backgroundColor: isSessionActive ? '#dc2626' : undefined,
                borderColor: isSessionActive ? '#dc2626' : undefined
              }}
            >
              {isSessionActive ? 'Stop Session' : 'Start Session'}
            </button>
          </div>
        </div>
      </div>

      {/* Alert Messages */}
      {alertVisible && (
        <div style={{ marginBottom: 'var(--spacing-4)' }}>
          <AlertMessage
            alertLevel={pusherDetected ? "warning" : alertLevel}
            tiltAngle={livePosture.tiltAngle}
            direction={livePosture.tiltDirection}
            onDismiss={() => setAlertVisible(false)}
            autoHide={true}
          />
        </div>
      )}

      {/* Main Session Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Live Posture Monitor */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            Live Posture Monitor
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-8)',
            backgroundColor: isSessionActive ? 'var(--primary-blue-50)' : 'var(--gray-50)',
            borderRadius: 'var(--radius-lg)',
            border: `2px ${isSessionActive ? 'solid var(--primary-blue-200)' : 'dashed var(--gray-200)'}`,
            minHeight: '250px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <PostureVisualization 
                tiltAngle={realTimeSensorData.imu.pitch}
                size={140}
                clinicalThresholds={thresholds}
                calibrationBaseline={baseline?.pitch || 0}
                pusherDetected={pusherDetected}
                connectionStatus={esp32Connected ? 'connected' : 'disconnected'}
              />
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: isSessionActive ? 'var(--primary-blue)' : 'var(--gray-500)',
                margin: 'var(--spacing-4) 0 0 0',
                fontWeight: '600'
              }}>
                {isSessionActive ? 'Monitoring Active' : 'Session Stopped'}
              </p>
              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-400)',
                margin: 'var(--spacing-1) 0 0 0'
              }}>
                {isSessionActive ? 
                  `Posture: ${livePosture.tiltDirection === 'center' ? 'Upright' : 
                    livePosture.tiltDirection === 'left_lean' ? 'Leaning Left' : 'Leaning Right'}` : 
                  'Start session to begin monitoring'}
              </p>
            </div>
          </div>
        </div>

        {/* Tilt Measurement */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            Tilt Measurement
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-6)',
            minHeight: '200px'
          }}>
            <CircularTiltMeter 
              tiltAngle={realTimeSensorData.imu.pitch}
              direction={livePosture.tiltDirection}
              size={160}
              clinicalThresholds={thresholds}
              calibratedBaseline={baseline?.pitch || 0}
              showClinicalMarkers={true}
            />
          </div>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-4)',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--radius-md)',
            marginTop: 'var(--spacing-4)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: '700',
              color: pusherDetected ? '#dc2626' : 
                     Math.abs(realTimeSensorData.imu.pitch) >= thresholds.severe ? '#dc2626' :
                     Math.abs(realTimeSensorData.imu.pitch) >= thresholds.normal ? '#f59e0b' : 
                     'var(--success-green)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {Math.abs(realTimeSensorData.imu.pitch).toFixed(1)}°
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              fontWeight: '500'
            }}>
              Current Tilt Angle
            </div>
            {pusherDetected && (
              <div style={{
                fontSize: 'var(--font-size-xs)',
                color: '#dc2626',
                fontWeight: '600',
                marginTop: 'var(--spacing-1)'
              }}>
                ⚠️ Pusher Syndrome Detected
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sensor Data Display */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-4)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          Live Sensor Data
        </h3>
        
        <SensorDataDisplay
          imuData={realTimeSensorData.imu}
          fsrData={realTimeSensorData.fsr}
          hapticActive={realTimeSensorData.hapticActive}
          isConnected={realTimeSensorData.isConnected}
          esp32Status={esp32Status}
          clinicalData={clinicalData}
          calibrationStatus={calibrationData}
          onStartCalibration={handleStartCalibration}
          onToggleDemoMode={handleToggleDemoMode}
        />
      </div>

      {/* Session Stats */}
      {isSessionActive && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)',
          marginBottom: 'var(--spacing-6)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
            </svg>
            Session Statistics
          </h3>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 'var(--spacing-4)'
          }}>
            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: Math.abs(livePosture.tiltAngle) <= thresholds.normal ? '#F0FDF4' : '#FEF2F2',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${Math.abs(livePosture.tiltAngle) <= thresholds.normal ? '#BBF7D0' : '#FECACA'}`
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: Math.abs(livePosture.tiltAngle) <= thresholds.normal ? 'var(--success-green)' : '#dc2626',
                marginBottom: 'var(--spacing-1)'
              }}>
                {Math.abs(livePosture.tiltAngle) <= thresholds.normal ? '✓' : '⚠️'}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Current Posture
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: 'var(--primary-blue-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--primary-blue-100)'
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: 'var(--primary-blue)',
                marginBottom: 'var(--spacing-1)'
              }}>
                {clinicalData.episodeCount}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Episodes Today
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: pusherDetected ? '#FEF2F2' : '#FEF3C7',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${pusherDetected ? '#FECACA' : '#FDE68A'}`
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: pusherDetected ? '#dc2626' : 'var(--warning-orange)',
                marginBottom: 'var(--spacing-1)'
              }}>
                {clinicalData.clinicalScore}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Clinical Score
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: esp32Connected ? '#F0FDF4' : '#FEF2F2',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${esp32Connected ? '#BBF7D0' : '#FECACA'}`
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: esp32Connected ? 'var(--success-green)' : '#dc2626',
                marginBottom: 'var(--spacing-1)'
              }}>
                {esp32Connected ? '●' : '○'}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Device Status
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionPage;