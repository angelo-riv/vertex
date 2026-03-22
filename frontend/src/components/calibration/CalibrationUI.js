import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import axios from 'axios';

/**
 * Calibration UI Component
 * 
 * Provides a complete calibration interface for ESP32 device baseline establishment.
 * Includes 30-second countdown timer, patient instructions, and calibration status display.
 * 
 * Requirements: 18.3, 18.4, 18.5 - Calibration UI and workflow
 */
const CalibrationUI = ({ 
  patientId,
  deviceId,
  onCalibrationComplete = () => {},
  onCalibrationCancel = () => {},
  showInstructions = true 
}) => {
  const { state, actions } = useApp();
  const [calibrationState, setCalibrationState] = useState('idle'); // 'idle', 'starting', 'active', 'completed', 'failed'
  const [countdown, setCountdown] = useState(30);
  const [calibrationData, setCalibrationData] = useState(null);
  const [error, setError] = useState(null);
  const [instructions, setInstructions] = useState('');

  // Get current calibration status from context
  const currentCalibration = state.calibration;
  const isCalibrated = currentCalibration.status === 'calibrated';
  const lastCalibrationDate = currentCalibration.lastCalibrationDate;

  useEffect(() => {
    // Update local state when context changes
    if (currentCalibration.status === 'calibrating') {
      setCalibrationState('active');
      setCountdown(30 - currentCalibration.progress);
    } else if (currentCalibration.status === 'calibrated') {
      setCalibrationState('completed');
      setCalibrationData(currentCalibration.baseline);
    }
  }, [currentCalibration]);

  // Countdown timer effect
  useEffect(() => {
    let timer;
    if (calibrationState === 'active' && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(prev => prev - 1);
        actions.updateCalibrationProgress(((30 - countdown + 1) / 30) * 100);
        
        // Update instructions based on countdown
        if (countdown > 20) {
          setInstructions('Stand upright and remain still. Calibration starting...');
        } else if (countdown > 10) {
          setInstructions('Keep standing straight. Do not move or lean.');
        } else if (countdown > 5) {
          setInstructions('Almost done! Stay perfectly still.');
        } else {
          setInstructions('Final seconds... maintain position.');
        }
      }, 1000);
    } else if (calibrationState === 'active' && countdown === 0) {
      completeCalibration();
    }

    return () => clearTimeout(timer);
  }, [calibrationState, countdown]);

  const startCalibration = async () => {
    try {
      setError(null);
      setCalibrationState('starting');
      setInstructions('Preparing calibration...');

      // Trigger ESP32 calibration mode
      const response = await axios.post('/api/calibration/start', {
        deviceId: deviceId || state.esp32.deviceId,
        patientId: patientId,
        duration: 30
      });

      if (response.data.success) {
        setCalibrationState('active');
        setCountdown(30);
        setInstructions('Stand upright and remain still. Calibration starting...');
        
        // Update context
        actions.updateCalibrationProgress(0);
        actions.setCalibrationDevice(deviceId || state.esp32.deviceId);
      } else {
        throw new Error(response.data.error || 'Failed to start calibration');
      }
    } catch (err) {
      setError(err.message);
      setCalibrationState('failed');
      setInstructions('Calibration failed. Please try again.');
    }
  };

  const completeCalibration = async () => {
    try {
      setInstructions('Processing calibration data...');
      
      // Get calibration results from backend
      const response = await axios.get(`/api/calibration/results/${deviceId || state.esp32.deviceId}`);
      
      if (response.data.success) {
        const baseline = response.data.baseline;
        setCalibrationData(baseline);
        setCalibrationState('completed');
        setInstructions('Calibration completed successfully!');
        
        // Update context with baseline data
        actions.setCalibrationBaseline(baseline);
        actions.setCalibrationActive(true);
        
        // Notify parent component
        onCalibrationComplete(baseline);
      } else {
        throw new Error(response.data.error || 'Failed to complete calibration');
      }
    } catch (err) {
      setError(err.message);
      setCalibrationState('failed');
      setInstructions('Failed to process calibration data.');
    }
  };

  const cancelCalibration = async () => {
    try {
      if (calibrationState === 'active') {
        await axios.post('/api/calibration/cancel', {
          deviceId: deviceId || state.esp32.deviceId
        });
      }
      
      setCalibrationState('idle');
      setCountdown(30);
      setInstructions('');
      setError(null);
      
      // Reset context
      actions.updateCalibrationProgress(0);
      
      onCalibrationCancel();
    } catch (err) {
      console.error('Error canceling calibration:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getCalibrationStatusColor = () => {
    switch (calibrationState) {
      case 'active': return '#2196F3';
      case 'completed': return '#4CAF50';
      case 'failed': return '#F44336';
      default: return '#757575';
    }
  };

  return (
    <div className="calibration-ui">
      <div className="calibration-header">
        <h3>Device Calibration</h3>
        <div className="calibration-status">
          <span 
            className="status-indicator"
            style={{ backgroundColor: getCalibrationStatusColor() }}
          />
          <span className="status-text">
            {calibrationState === 'idle' && 'Ready to calibrate'}
            {calibrationState === 'starting' && 'Starting calibration...'}
            {calibrationState === 'active' && `Calibrating... ${countdown}s`}
            {calibrationState === 'completed' && 'Calibration complete'}
            {calibrationState === 'failed' && 'Calibration failed'}
          </span>
        </div>
      </div>

      {/* Current Calibration Status */}
      <div className="current-status">
        <div className="status-row">
          <span className="label">Device:</span>
          <span className="value">{deviceId || state.esp32.deviceId || 'Not connected'}</span>
        </div>
        <div className="status-row">
          <span className="label">Last Calibration:</span>
          <span className="value">{formatDate(lastCalibrationDate)}</span>
        </div>
        <div className="status-row">
          <span className="label">Status:</span>
          <span className={`value ${isCalibrated ? 'calibrated' : 'not-calibrated'}`}>
            {isCalibrated ? 'Calibrated' : 'Not Calibrated'}
          </span>
        </div>
      </div>

      {/* Calibration Instructions */}
      {showInstructions && (calibrationState === 'active' || calibrationState === 'starting') && (
        <div className="calibration-instructions">
          <div className="instruction-icon">
            {calibrationState === 'active' ? '🧍' : '⏳'}
          </div>
          <p className="instruction-text">{instructions}</p>
          
          {calibrationState === 'active' && (
            <div className="progress-container">
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${((30 - countdown) / 30) * 100}%` }}
                />
              </div>
              <div className="progress-text">
                {Math.round(((30 - countdown) / 30) * 100)}% Complete
              </div>
            </div>
          )}
        </div>
      )}

      {/* Calibration Results */}
      {calibrationState === 'completed' && calibrationData && (
        <div className="calibration-results">
          <h4>Calibration Results</h4>
          <div className="results-grid">
            <div className="result-item">
              <span className="result-label">Baseline Pitch:</span>
              <span className="result-value">{calibrationData.pitch?.toFixed(2)}°</span>
            </div>
            <div className="result-item">
              <span className="result-label">FSR Left:</span>
              <span className="result-value">{calibrationData.fsrLeft}</span>
            </div>
            <div className="result-item">
              <span className="result-label">FSR Right:</span>
              <span className="result-value">{calibrationData.fsrRight}</span>
            </div>
            <div className="result-item">
              <span className="result-label">Balance Ratio:</span>
              <span className="result-value">{calibrationData.ratio?.toFixed(2)}</span>
            </div>
            <div className="result-item">
              <span className="result-label">Stability:</span>
              <span className="result-value">±{calibrationData.stdDev?.toFixed(2)}°</span>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="calibration-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="calibration-actions">
        {calibrationState === 'idle' && (
          <button 
            className="btn btn-primary calibration-btn"
            onClick={startCalibration}
            disabled={!state.esp32.isConnected}
          >
            {isCalibrated ? 'Recalibrate Device' : 'Start Calibration'}
          </button>
        )}
        
        {(calibrationState === 'starting' || calibrationState === 'active') && (
          <button 
            className="btn btn-secondary calibration-btn"
            onClick={cancelCalibration}
          >
            Cancel Calibration
          </button>
        )}
        
        {calibrationState === 'completed' && (
          <button 
            className="btn btn-success calibration-btn"
            onClick={() => setCalibrationState('idle')}
          >
            Done
          </button>
        )}
        
        {calibrationState === 'failed' && (
          <button 
            className="btn btn-primary calibration-btn"
            onClick={() => setCalibrationState('idle')}
          >
            Try Again
          </button>
        )}
      </div>

      {/* Device Connection Warning */}
      {!state.esp32.isConnected && (
        <div className="connection-warning">
          <span className="warning-icon">📡</span>
          <span className="warning-text">
            ESP32 device must be connected to perform calibration
          </span>
        </div>
      )}

      <style jsx>{`
        .calibration-ui {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          max-width: 500px;
          margin: 0 auto;
        }

        .calibration-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #eee;
        }

        .calibration-header h3 {
          margin: 0;
          color: #333;
        }

        .calibration-status {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          display: inline-block;
        }

        .status-text {
          font-size: 14px;
          color: #666;
        }

        .current-status {
          margin-bottom: 20px;
        }

        .status-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .status-row .label {
          font-weight: 500;
          color: #666;
        }

        .status-row .value {
          color: #333;
        }

        .status-row .value.calibrated {
          color: #4CAF50;
          font-weight: 500;
        }

        .status-row .value.not-calibrated {
          color: #F44336;
          font-weight: 500;
        }

        .calibration-instructions {
          background: #f5f5f5;
          border-radius: 8px;
          padding: 20px;
          text-align: center;
          margin-bottom: 20px;
        }

        .instruction-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }

        .instruction-text {
          font-size: 16px;
          color: #333;
          margin-bottom: 15px;
          line-height: 1.5;
        }

        .progress-container {
          margin-top: 15px;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 8px;
        }

        .progress-fill {
          height: 100%;
          background: #2196F3;
          transition: width 0.3s ease;
        }

        .progress-text {
          font-size: 14px;
          color: #666;
        }

        .calibration-results {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 20px;
        }

        .calibration-results h4 {
          margin: 0 0 15px 0;
          color: #333;
        }

        .results-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .result-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .result-label {
          font-size: 12px;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .result-value {
          font-size: 16px;
          font-weight: 500;
          color: #333;
        }

        .calibration-error {
          background: #ffebee;
          border: 1px solid #ffcdd2;
          border-radius: 4px;
          padding: 12px;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .error-icon {
          font-size: 18px;
        }

        .error-text {
          color: #c62828;
          font-size: 14px;
        }

        .calibration-actions {
          display: flex;
          gap: 12px;
          justify-content: center;
        }

        .calibration-btn {
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 140px;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1976D2;
        }

        .btn-secondary {
          background: #757575;
          color: white;
        }

        .btn-secondary:hover {
          background: #616161;
        }

        .btn-success {
          background: #4CAF50;
          color: white;
        }

        .btn-success:hover {
          background: #388E3C;
        }

        .calibration-btn:disabled {
          background: #e0e0e0;
          color: #9e9e9e;
          cursor: not-allowed;
        }

        .connection-warning {
          background: #fff3cd;
          border: 1px solid #ffeaa7;
          border-radius: 4px;
          padding: 12px;
          margin-top: 15px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .warning-icon {
          font-size: 18px;
        }

        .warning-text {
          color: #856404;
          font-size: 14px;
        }

        @media (max-width: 480px) {
          .calibration-ui {
            padding: 15px;
          }

          .results-grid {
            grid-template-columns: 1fr;
          }

          .calibration-actions {
            flex-direction: column;
          }

          .calibration-btn {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default CalibrationUI;