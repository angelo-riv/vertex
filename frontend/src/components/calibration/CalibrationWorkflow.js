import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import CalibrationUI from './CalibrationUI';
import ThresholdConfiguration from '../clinical/ThresholdConfiguration';
import axios from 'axios';

/**
 * Calibration Workflow Component
 * 
 * Integrates calibration data with patient-specific threshold settings.
 * Shows calibration history and improvement in detection accuracy.
 * 
 * Requirements: 18.6, 18.7 - Calibration workflow integration
 */
const CalibrationWorkflow = ({ 
  patientId,
  onWorkflowComplete = () => {},
  showHistory = true 
}) => {
  const { state, actions } = useApp();
  const [currentStep, setCurrentStep] = useState(1); // 1: Calibrate, 2: Configure Thresholds, 3: Review
  const [calibrationHistory, setCalibrationHistory] = useState([]);
  const [thresholds, setThresholds] = useState(null);
  const [accuracyImprovement, setAccuracyImprovement] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (patientId) {
      loadCalibrationHistory();
      loadCurrentThresholds();
    }
  }, [patientId]);

  const loadCalibrationHistory = async () => {
    try {
      const response = await axios.get(`/api/calibration/history/${patientId}`);
      if (response.data.success) {
        setCalibrationHistory(response.data.calibrations);
      }
    } catch (err) {
      console.error('Error loading calibration history:', err);
    }
  };

  const loadCurrentThresholds = async () => {
    try {
      const response = await axios.get(`/api/clinical/thresholds/${patientId}`);
      if (response.data.success) {
        setThresholds(response.data.thresholds);
      }
    } catch (err) {
      console.error('Error loading thresholds:', err);
    }
  };

  const handleCalibrationComplete = async (baseline) => {
    try {
      setLoading(true);
      
      // Calculate accuracy improvement
      const improvement = await calculateAccuracyImprovement(baseline);
      setAccuracyImprovement(improvement);
      
      // Move to threshold configuration step
      setCurrentStep(2);
      
      // Reload history to show new calibration
      await loadCalibrationHistory();
      
    } catch (err) {
      setError('Failed to process calibration completion');
      console.error('Calibration completion error:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateAccuracyImprovement = async (newBaseline) => {
    try {
      const response = await axios.post('/api/calibration/accuracy-analysis', {
        patientId,
        newBaseline,
        previousCalibrations: calibrationHistory
      });
      
      if (response.data.success) {
        return response.data.improvement;
      }
      return null;
    } catch (err) {
      console.error('Error calculating accuracy improvement:', err);
      return null;
    }
  };

  const handleThresholdsSaved = async (newThresholds) => {
    try {
      setThresholds(newThresholds);
      
      // Apply calibrated thresholds
      await applyCalibrationToThresholds(newThresholds);
      
      // Move to review step
      setCurrentStep(3);
      
    } catch (err) {
      setError('Failed to apply calibrated thresholds');
      console.error('Threshold application error:', err);
    }
  };

  const applyCalibrationToThresholds = async (thresholds) => {
    try {
      const calibrationBaseline = state.calibration.baseline;
      if (!calibrationBaseline) return;

      // Calculate calibration-adjusted thresholds
      const adjustedThresholds = {
        ...thresholds,
        normal: Math.max(3.0, thresholds.normal - Math.abs(calibrationBaseline.pitch)),
        pusher: Math.max(5.0, thresholds.pusher - Math.abs(calibrationBaseline.pitch)),
        severe: Math.max(10.0, thresholds.severe - Math.abs(calibrationBaseline.pitch)),
        calibrationAdjusted: true,
        baselinePitch: calibrationBaseline.pitch,
        baselineRatio: calibrationBaseline.ratio
      };

      // Save adjusted thresholds
      await axios.put(`/api/clinical/thresholds/${patientId}`, adjustedThresholds);
      
      // Update context
      actions.setClinicalThresholds(adjustedThresholds);
      
    } catch (err) {
      console.error('Error applying calibration to thresholds:', err);
      throw err;
    }
  };

  const completeWorkflow = () => {
    onWorkflowComplete({
      calibration: state.calibration.baseline,
      thresholds: thresholds,
      accuracyImprovement: accuracyImprovement
    });
  };

  const resetWorkflow = () => {
    setCurrentStep(1);
    setError(null);
    setAccuracyImprovement(null);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStepStatus = (step) => {
    if (step < currentStep) return 'completed';
    if (step === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="calibration-workflow">
      {/* Progress Steps */}
      <div className="workflow-steps">
        <div className={`step ${getStepStatus(1)}`}>
          <div className="step-number">1</div>
          <div className="step-label">Device Calibration</div>
        </div>
        <div className="step-connector" />
        <div className={`step ${getStepStatus(2)}`}>
          <div className="step-number">2</div>
          <div className="step-label">Configure Thresholds</div>
        </div>
        <div className="step-connector" />
        <div className={`step ${getStepStatus(3)}`}>
          <div className="step-number">3</div>
          <div className="step-label">Review & Complete</div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="workflow-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button className="error-dismiss" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Step Content */}
      <div className="workflow-content">
        {currentStep === 1 && (
          <div className="step-content">
            <h3>Step 1: Device Calibration</h3>
            <p>First, we need to establish a baseline for your posture and weight distribution.</p>
            
            <CalibrationUI
              patientId={patientId}
              deviceId={state.esp32.deviceId}
              onCalibrationComplete={handleCalibrationComplete}
              showInstructions={true}
            />
          </div>
        )}

        {currentStep === 2 && (
          <div className="step-content">
            <h3>Step 2: Configure Clinical Thresholds</h3>
            <p>Now we'll set up personalized thresholds based on your calibration data.</p>
            
            {accuracyImprovement && (
              <div className="accuracy-improvement">
                <h4>Calibration Impact</h4>
                <div className="improvement-stats">
                  <div className="stat">
                    <span className="stat-label">Detection Accuracy:</span>
                    <span className="stat-value">
                      {accuracyImprovement.before?.toFixed(1)}% → {accuracyImprovement.after?.toFixed(1)}%
                    </span>
                    <span className="stat-change positive">
                      +{(accuracyImprovement.after - accuracyImprovement.before).toFixed(1)}%
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">False Positives:</span>
                    <span className="stat-value">
                      {accuracyImprovement.falsePositivesBefore} → {accuracyImprovement.falsePositivesAfter}
                    </span>
                    <span className="stat-change positive">
                      -{accuracyImprovement.falsePositivesBefore - accuracyImprovement.falsePositivesAfter}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            <ThresholdConfiguration
              patientId={patientId}
              onSave={handleThresholdsSaved}
              calibrationBaseline={state.calibration.baseline}
              showCalibrationAdjustments={true}
            />
          </div>
        )}

        {currentStep === 3 && (
          <div className="step-content">
            <h3>Step 3: Review & Complete</h3>
            <p>Review your calibration and threshold settings.</p>
            
            <div className="workflow-summary">
              <div className="summary-section">
                <h4>Calibration Summary</h4>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">Baseline Pitch:</span>
                    <span className="summary-value">
                      {state.calibration.baseline?.pitch?.toFixed(2)}°
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Balance Ratio:</span>
                    <span className="summary-value">
                      {state.calibration.baseline?.ratio?.toFixed(2)}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Stability:</span>
                    <span className="summary-value">
                      ±{state.calibration.baseline?.stdDev?.toFixed(2)}°
                    </span>
                  </div>
                </div>
              </div>

              <div className="summary-section">
                <h4>Clinical Thresholds</h4>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">Normal Range:</span>
                    <span className="summary-value">±{thresholds?.normal}°</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Pusher Threshold:</span>
                    <span className="summary-value">±{thresholds?.pusher}°</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">Severe Threshold:</span>
                    <span className="summary-value">±{thresholds?.severe}°</span>
                  </div>
                </div>
              </div>

              {accuracyImprovement && (
                <div className="summary-section">
                  <h4>Expected Improvement</h4>
                  <div className="improvement-summary">
                    <div className="improvement-metric">
                      <span className="metric-value">
                        +{(accuracyImprovement.after - accuracyImprovement.before).toFixed(1)}%
                      </span>
                      <span className="metric-label">Detection Accuracy</span>
                    </div>
                    <div className="improvement-metric">
                      <span className="metric-value">
                        -{accuracyImprovement.falsePositivesBefore - accuracyImprovement.falsePositivesAfter}
                      </span>
                      <span className="metric-label">Fewer False Alarms</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="workflow-actions">
              <button className="btn btn-secondary" onClick={resetWorkflow}>
                Start Over
              </button>
              <button className="btn btn-primary" onClick={completeWorkflow}>
                Complete Setup
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Calibration History */}
      {showHistory && calibrationHistory.length > 0 && (
        <div className="calibration-history">
          <h4>Calibration History</h4>
          <div className="history-list">
            {calibrationHistory.slice(0, 5).map((calibration, index) => (
              <div key={calibration.id} className="history-item">
                <div className="history-date">
                  {formatDate(calibration.calibration_date)}
                </div>
                <div className="history-details">
                  <span>Pitch: {calibration.baseline_pitch?.toFixed(2)}°</span>
                  <span>Ratio: {calibration.baseline_ratio?.toFixed(2)}</span>
                  <span className={calibration.is_active ? 'active' : 'inactive'}>
                    {calibration.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .calibration-workflow {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .workflow-steps {
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 40px;
          padding: 20px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .step {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .step-number {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 16px;
          transition: all 0.3s ease;
        }

        .step.pending .step-number {
          background: #e0e0e0;
          color: #9e9e9e;
        }

        .step.active .step-number {
          background: #2196F3;
          color: white;
        }

        .step.completed .step-number {
          background: #4CAF50;
          color: white;
        }

        .step-label {
          font-size: 14px;
          font-weight: 500;
          text-align: center;
          color: #666;
        }

        .step.active .step-label {
          color: #2196F3;
        }

        .step.completed .step-label {
          color: #4CAF50;
        }

        .step-connector {
          width: 60px;
          height: 2px;
          background: #e0e0e0;
          margin: 0 20px;
        }

        .workflow-error {
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
          flex: 1;
        }

        .error-dismiss {
          background: none;
          border: none;
          font-size: 18px;
          color: #c62828;
          cursor: pointer;
          padding: 0;
          width: 20px;
          height: 20px;
        }

        .workflow-content {
          background: white;
          border-radius: 8px;
          padding: 30px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-bottom: 20px;
        }

        .step-content h3 {
          margin: 0 0 10px 0;
          color: #333;
        }

        .step-content p {
          color: #666;
          margin-bottom: 30px;
          line-height: 1.5;
        }

        .accuracy-improvement {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 30px;
        }

        .accuracy-improvement h4 {
          margin: 0 0 15px 0;
          color: #333;
        }

        .improvement-stats {
          display: flex;
          gap: 30px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .stat-label {
          font-size: 12px;
          color: #666;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .stat-value {
          font-size: 16px;
          font-weight: 500;
          color: #333;
        }

        .stat-change {
          font-size: 14px;
          font-weight: 500;
        }

        .stat-change.positive {
          color: #4CAF50;
        }

        .workflow-summary {
          display: flex;
          flex-direction: column;
          gap: 30px;
        }

        .summary-section h4 {
          margin: 0 0 15px 0;
          color: #333;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .summary-item {
          display: flex;
          justify-content: space-between;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 4px;
        }

        .summary-label {
          color: #666;
          font-size: 14px;
        }

        .summary-value {
          color: #333;
          font-weight: 500;
        }

        .improvement-summary {
          display: flex;
          gap: 30px;
        }

        .improvement-metric {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .metric-value {
          font-size: 24px;
          font-weight: bold;
          color: #4CAF50;
        }

        .metric-label {
          font-size: 14px;
          color: #666;
          text-align: center;
        }

        .workflow-actions {
          display: flex;
          gap: 15px;
          justify-content: center;
          margin-top: 30px;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          min-width: 120px;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover {
          background: #1976D2;
        }

        .btn-secondary {
          background: #757575;
          color: white;
        }

        .btn-secondary:hover {
          background: #616161;
        }

        .calibration-history {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .calibration-history h4 {
          margin: 0 0 15px 0;
          color: #333;
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .history-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 4px;
        }

        .history-date {
          font-size: 14px;
          color: #666;
        }

        .history-details {
          display: flex;
          gap: 15px;
          font-size: 14px;
        }

        .history-details span.active {
          color: #4CAF50;
          font-weight: 500;
        }

        .history-details span.inactive {
          color: #757575;
        }

        @media (max-width: 768px) {
          .workflow-steps {
            flex-direction: column;
            gap: 20px;
          }

          .step-connector {
            width: 2px;
            height: 30px;
            margin: 0;
          }

          .improvement-stats,
          .improvement-summary {
            flex-direction: column;
            gap: 15px;
          }

          .summary-grid {
            grid-template-columns: 1fr;
          }

          .workflow-actions {
            flex-direction: column;
          }

          .btn {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
};

export default CalibrationWorkflow;