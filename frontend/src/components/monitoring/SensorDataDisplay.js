import React from 'react';

const SensorDataDisplay = ({ 
  imuData = { pitch: 0, roll: 0, yaw: 0 },
  fsrData = { left: 0, right: 0 },
  hapticActive = false,
  isConnected = false
}) => {
  // Calculate FSR balance (-1 to 1, left to right bias)
  const calculateBalance = () => {
    const total = fsrData.left + fsrData.right;
    if (total === 0) return 0;
    return ((fsrData.right - fsrData.left) / total);
  };

  const balance = calculateBalance();

  // Format sensor values for display
  const formatValue = (value, unit = '°', decimals = 1) => {
    if (!isConnected) return '--';
    return `${value.toFixed(decimals)}${unit}`;
  };

  const formatFSR = (value) => {
    if (!isConnected) return '--';
    return value.toFixed(0);
  };

  const formatBalance = () => {
    if (!isConnected) return '--';
    const absBalance = Math.abs(balance);
    const direction = balance > 0.1 ? 'R' : balance < -0.1 ? 'L' : 'C';
    return `${(absBalance * 100).toFixed(0)}% ${direction}`;
  };

  // Connection status indicator
  const ConnectionStatus = () => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--spacing-2)',
      marginBottom: 'var(--spacing-4)',
      padding: 'var(--spacing-3)',
      backgroundColor: isConnected ? 'var(--primary-blue-50)' : 'var(--gray-50)',
      borderRadius: 'var(--border-radius-md)',
      border: `1px solid ${isConnected ? 'var(--primary-blue-200)' : 'var(--gray-200)'}`
    }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: isConnected ? 'var(--primary-blue)' : 'var(--gray-400)',
        animation: isConnected ? 'pulse 2s infinite' : 'none'
      }} />
      <span style={{
        fontSize: 'var(--font-size-sm)',
        fontWeight: '500',
        color: isConnected ? 'var(--primary-blue-700)' : 'var(--gray-600)'
      }}>
        {isConnected ? 'Device Connected' : 'Device Disconnected'}
      </span>
      
      {/* Pulse animation for connected state */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </div>
  );

  return (
    <div>
      <ConnectionStatus />
      
      {/* IMU Sensor Data */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--border-radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-3)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            backgroundColor: 'var(--primary-blue)',
            borderRadius: '2px'
          }} />
          IMU Orientation
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--spacing-3)'
        }}>
          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatValue(imuData.pitch)}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Pitch
            </div>
          </div>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatValue(imuData.roll)}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Roll
            </div>
          </div>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatValue(imuData.yaw)}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Yaw
            </div>
          </div>
        </div>
      </div>

      {/* FSR Sensor Data */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--border-radius-lg)',
        padding: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-4)',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-3)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            backgroundColor: 'var(--primary-blue)',
            borderRadius: '2px'
          }} />
          Weight Distribution
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--spacing-3)'
        }}>
          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatFSR(fsrData.left)}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Left FSR
            </div>
          </div>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatFSR(fsrData.right)}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Right FSR
            </div>
          </div>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-3)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '700',
              color: 'var(--primary-blue)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {formatBalance()}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Balance
            </div>
          </div>
        </div>
      </div>

      {/* Haptic Feedback Status */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--border-radius-lg)',
        padding: 'var(--spacing-4)',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-3)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            backgroundColor: 'var(--primary-blue)',
            borderRadius: '2px'
          }} />
          Haptic Feedback
        </h3>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-3)',
          padding: 'var(--spacing-3)',
          backgroundColor: hapticActive ? '#fef3c7' : 'var(--primary-blue-50)',
          borderRadius: 'var(--border-radius-md)',
          border: `1px solid ${hapticActive ? '#fcd34d' : 'var(--primary-blue-200)'}`
        }}>
          <div style={{
            width: '16px',
            height: '16px',
            borderRadius: '50%',
            backgroundColor: hapticActive ? '#f59e0b' : 'var(--primary-blue)',
            animation: hapticActive ? 'vibrate 0.5s infinite' : 'none'
          }} />
          
          <div>
            <div style={{
              fontSize: 'var(--font-size-base)',
              fontWeight: '600',
              color: hapticActive ? '#92400e' : 'var(--primary-blue-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              {hapticActive ? 'Active' : 'Inactive'}
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: hapticActive ? '#a16207' : 'var(--primary-blue-600)'
            }}>
              {hapticActive ? 'Corrective feedback in progress' : 'No correction needed'}
            </div>
          </div>
          
          {/* Vibration animation */}
          <style>
            {`
              @keyframes vibrate {
                0%, 100% { transform: translateX(0); }
                25% { transform: translateX(-2px); }
                75% { transform: translateX(2px); }
              }
            `}
          </style>
        </div>
      </div>
    </div>
  );
};

export default SensorDataDisplay;