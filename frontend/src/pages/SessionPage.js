import React, { useState } from 'react';
import PostureVisualization from '../components/monitoring/PostureVisualization';
import CircularTiltMeter from '../components/monitoring/CircularTiltMeter';
import SensorDataDisplay from '../components/monitoring/SensorDataDisplay';
import AlertMessage from '../components/monitoring/AlertMessage';

const SessionPage = () => {
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [alertVisible, setAlertVisible] = useState(false);

  // Mock sensor data (in real app, this would come from API)
  const mockSensorData = {
    imu: { pitch: 0.5, roll: -1.2, yaw: 0.8 },
    fsr: { left: 245, right: 267 },
    isConnected: false,
    hapticActive: false,
    alertLevel: 'safe'
  };

  const handleStartSession = () => {
    setIsSessionActive(true);
    // TODO: Implement actual session start logic
  };

  const handleStopSession = () => {
    setIsSessionActive(false);
    setSessionDuration(0);
    // TODO: Implement actual session stop logic
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
            alertLevel="warning"
            tiltAngle={5.2}
            direction="left"
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
                postureState="upright" 
                tiltAngle={0}
                size={140}
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
                {isSessionActive ? 'Posture: Upright' : 'Start session to begin monitoring'}
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
              tiltAngle={0}
              direction="center"
              size={160}
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
              color: 'var(--success-green)',
              marginBottom: 'var(--spacing-1)'
            }}>
              0.0°
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              fontWeight: '500'
            }}>
              Current Tilt Angle
            </div>
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
          imuData={mockSensorData.imu}
          fsrData={mockSensorData.fsr}
          hapticActive={mockSensorData.hapticActive}
          isConnected={mockSensorData.isConnected}
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
              backgroundColor: 'var(--success-green)'.replace('var(--success-green)', '#F0FDF4'),
              borderRadius: 'var(--radius-md)',
              border: '1px solid #BBF7D0'
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: 'var(--success-green)',
                marginBottom: 'var(--spacing-1)'
              }}>
                100%
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Upright Time
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
                0
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Corrections
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: '#FEF3C7',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #FDE68A'
            }}>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: 'var(--warning-orange)',
                marginBottom: 'var(--spacing-1)'
              }}>
                0.0°
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Average Tilt
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionPage;