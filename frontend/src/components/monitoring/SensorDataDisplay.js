import React, { useState, useEffect, memo } from 'react';
import ConnectionFallback from './ConnectionFallback';

const SensorDataDisplay = ({ 
  imuData = { pitch: 0, roll: 0, yaw: 0 },
  fsrData = { left: 0, right: 0 },
  hapticActive = false,
  isConnected = false,
  // ESP32 Integration props
  esp32Status = {
    isConnected: false,
    deviceId: null,
    lastDataTimestamp: null,
    connectionQuality: 'unknown', // 'excellent', 'good', 'poor', 'disconnected'
    demoMode: false
  },
  // Clinical Analytics props
  clinicalData = {
    pusherDetected: false,
    currentEpisode: null,
    clinicalScore: 0, // BLS/4PPS compatible score (0-3)
    confidence: 0,
    episodeCount: 0
  },
  // Calibration props
  calibrationStatus = {
    status: 'not_calibrated', // 'not_calibrated', 'calibrating', 'calibrated'
    progress: 0, // 0-100 for 30-second calibration
    baseline: null,
    lastCalibrationDate: null
  },
  // Event handlers
  onStartCalibration = () => {},
  onToggleDemoMode = () => {}
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
    if (!isConnected && !esp32Status.isConnected) return '--';
    return `${value.toFixed(decimals)}${unit}`;
  };

  const formatFSR = (value) => {
    if (!isConnected && !esp32Status.isConnected) return '--';
    return value.toFixed(0);
  };

  const formatBalance = () => {
    if (!isConnected && !esp32Status.isConnected) return '--';
    const absBalance = Math.abs(balance);
    const direction = balance > 0.1 ? 'R' : balance < -0.1 ? 'L' : 'C';
    return `${(absBalance * 100).toFixed(0)}% ${direction}`;
  };

  // Calculate data freshness
  const getDataFreshness = () => {
    if (!esp32Status.lastDataTimestamp) return 'No data';
    const now = new Date();
    const lastUpdate = new Date(esp32Status.lastDataTimestamp);
    const diffSeconds = Math.floor((now - lastUpdate) / 1000);
    
    if (diffSeconds < 5) return 'Live';
    if (diffSeconds < 30) return `${diffSeconds}s ago`;
    if (diffSeconds < 300) return `${Math.floor(diffSeconds / 60)}m ago`;
    return 'Stale data';
  };

  // Get connection quality color
  const getConnectionQualityColor = () => {
    switch (esp32Status.connectionQuality) {
      case 'excellent': return '#10b981'; // green-500
      case 'good': return '#3b82f6'; // blue-500
      case 'poor': return '#f59e0b'; // amber-500
      case 'disconnected': return '#ef4444'; // red-500
      default: return '#6b7280'; // gray-500
    }
  };

  // Get clinical severity color
  const getClinicalSeverityColor = (score) => {
    switch (score) {
      case 0: return '#10b981'; // green-500 - No pushing
      case 1: return '#f59e0b'; // amber-500 - Mild
      case 2: return '#f97316'; // orange-500 - Moderate
      case 3: return '#ef4444'; // red-500 - Severe
      default: return '#6b7280'; // gray-500
    }
  };

  // Get clinical severity label
  const getClinicalSeverityLabel = (score) => {
    switch (score) {
      case 0: return 'No Pushing';
      case 1: return 'Mild';
      case 2: return 'Moderate';
      case 3: return 'Severe';
      default: return 'Unknown';
    }
  };

  // Format calibration date
  const formatCalibrationDate = (date) => {
    if (!date) return 'Never';
    const calibrationDate = new Date(date);
    const now = new Date();
    const diffDays = Math.floor((now - calibrationDate) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return calibrationDate.toLocaleDateString();
  };

  // Enhanced Connection Status with ESP32 integration
  const ConnectionStatus = () => {
    return (
      <ConnectionFallback 
        onDemoModeActivate={onToggleDemoMode}
        showInternetStatus={false}
        className="sensor-display-connection"
      />
    );
  };

  // Clinical Pusher Detection Alert
  const ClinicalAlert = () => {
    if (!clinicalData.pusherDetected) return null;
    
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-3)',
        marginBottom: 'var(--spacing-4)',
        padding: 'var(--spacing-3)',
        backgroundColor: '#fef2f2',
        borderRadius: 'var(--border-radius-md)',
        border: '1px solid #fecaca'
      }}>
        <div style={{
          fontSize: 'var(--font-size-lg)',
          color: '#dc2626'
        }}>
          ⚠️
        </div>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: '600',
            color: '#dc2626',
            marginBottom: 'var(--spacing-1)'
          }}>
            Pusher Syndrome Detected
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: '#991b1b'
          }}>
            Severity: {getClinicalSeverityLabel(clinicalData.clinicalScore)} | 
            Confidence: {(clinicalData.confidence * 100).toFixed(0)}% |
            Episodes today: {clinicalData.episodeCount}
          </div>
        </div>
      </div>
    );
  };

  // Calibration Status and Controls
  const CalibrationSection = () => (
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
        Device Calibration
      </h3>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 'var(--spacing-3)'
      }}>
        <div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: '500',
            color: 'var(--gray-700)',
            marginBottom: 'var(--spacing-1)'
          }}>
            Status: {calibrationStatus.status === 'calibrated' ? 'Calibrated' : 
                     calibrationStatus.status === 'calibrating' ? 'Calibrating...' : 'Not Calibrated'}
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--gray-500)'
          }}>
            Last calibration: {formatCalibrationDate(calibrationStatus.lastCalibrationDate)}
          </div>
        </div>
        
        <button
          onClick={onStartCalibration}
          disabled={calibrationStatus.status === 'calibrating' || !esp32Status.isConnected}
          style={{
            padding: 'var(--spacing-2) var(--spacing-3)',
            backgroundColor: calibrationStatus.status === 'calibrating' ? 'var(--gray-400)' : 'var(--primary-blue)',
            color: 'white',
            border: 'none',
            borderRadius: 'var(--border-radius-md)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: '500',
            cursor: calibrationStatus.status === 'calibrating' || !esp32Status.isConnected ? 'not-allowed' : 'pointer',
            opacity: calibrationStatus.status === 'calibrating' || !esp32Status.isConnected ? 0.6 : 1
          }}
        >
          {calibrationStatus.status === 'calibrating' ? 'Calibrating...' : 'Start Calibration'}
        </button>
      </div>

      {/* Calibration progress bar */}
      {calibrationStatus.status === 'calibrating' && (
        <div style={{
          marginBottom: 'var(--spacing-3)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 'var(--spacing-1)'
          }}>
            <span style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-600)'
            }}>
              Calibration Progress
            </span>
            <span style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-600)'
            }}>
              {calibrationStatus.progress}%
            </span>
          </div>
          <div style={{
            width: '100%',
            height: '6px',
            backgroundColor: 'var(--gray-200)',
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${calibrationStatus.progress}%`,
              height: '100%',
              backgroundColor: 'var(--primary-blue)',
              transition: 'width 0.3s ease-in-out'
            }} />
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--gray-500)',
            marginTop: 'var(--spacing-1)',
            textAlign: 'center'
          }}>
            Please maintain normal upright posture during calibration
          </div>
        </div>
      )}

      {/* Baseline values display */}
      {calibrationStatus.baseline && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--spacing-2)',
          padding: 'var(--spacing-2)',
          backgroundColor: 'var(--gray-50)',
          borderRadius: 'var(--border-radius-md)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginBottom: '2px'
            }}>
              Baseline Pitch
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)'
            }}>
              {calibrationStatus.baseline.pitch?.toFixed(1)}°
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginBottom: '2px'
            }}>
              FSR Ratio
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)'
            }}>
              {calibrationStatus.baseline.fsrRatio?.toFixed(2)}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginBottom: '2px'
            }}>
              Std Dev
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)'
            }}>
              ±{calibrationStatus.baseline.stdDev?.toFixed(1)}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div>
      <ConnectionStatus />
      <ClinicalAlert />
      <CalibrationSection />
      
      {/* Clinical Scoring Display */}
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
          Clinical Assessment
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
              color: getClinicalSeverityColor(clinicalData.clinicalScore),
              marginBottom: 'var(--spacing-1)'
            }}>
              {clinicalData.clinicalScore}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              BLS Score
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
              {(clinicalData.confidence * 100).toFixed(0)}%
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Confidence
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
              {clinicalData.episodeCount}
            </div>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--primary-blue-700)',
              fontWeight: '500'
            }}>
              Episodes Today
            </div>
          </div>
        </div>
      </div>
      
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

      {/* FSR Sensor Data - Preserved existing layout */}
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
        </div>
      </div>
      
      {/* CSS Animations */}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          
          @keyframes vibrate {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-2px); }
            75% { transform: translateX(2px); }
          }
        `}
      </style>
    </div>
  );
};

export default memo(SensorDataDisplay);