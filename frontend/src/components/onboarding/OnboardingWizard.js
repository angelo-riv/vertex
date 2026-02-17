import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import ProgressBar from '../common/ProgressBar';
import WelcomeStep from './steps/WelcomeStep';
import StrokeSideStep from './steps/StrokeSideStep';
import SeverityStep from './steps/SeverityStep';
import MobilityStep from './steps/MobilityStep';
import TimelineStep from './steps/TimelineStep';

const OnboardingWizard = ({ onComplete }) => {
  const { state, actions } = useApp();
  const [currentStep, setCurrentStep] = useState(1);
  const [assessmentData, setAssessmentData] = useState({
    strokeSide: null,
    severityLevel: null,
    mobilityLevel: null,
    strokeTimeline: null,
    therapyStatus: null
  });
  const [loading, setLoading] = useState(false);

  const totalSteps = 5;

  const updateAssessmentData = (field, value) => {
    setAssessmentData(prev => ({
      ...prev,
      [field]: value
    }));
    actions.updateAssessmentData({ [field]: value });
  };

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(prev => prev + 1);
      actions.setOnboardingStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
      actions.setOnboardingStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    
    try {
      // Generate calibration settings based on assessment data
      const calibrationSettings = generateCalibrationSettings(assessmentData);
      
      // Update patient profile with assessment data
      const patientId = state.user?.id;
      if (patientId) {
        // Update patient profile
        const profileUpdates = {
          stroke_side: assessmentData.strokeSide,
          severity_level: assessmentData.severityLevel,
          mobility_level: assessmentData.mobilityLevel,
          stroke_timeline: getStrokeTimelineMonths(assessmentData.strokeTimeline),
          therapy_status: assessmentData.therapyStatus
        };
        
        await fetch(`/api/patients/${patientId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(profileUpdates)
        });
        
        // Save calibration settings
        const calibrationData = {
          patient_id: patientId,
          baseline_pitch: calibrationSettings.baselinePitch,
          baseline_roll: calibrationSettings.baselineRoll,
          warning_threshold: calibrationSettings.warningThreshold,
          danger_threshold: calibrationSettings.dangerThreshold
        };
        
        await fetch('/api/device/calibrate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(calibrationData)
        });
      }
      
      // Mark onboarding as complete
      actions.completeOnboarding();
      actions.updateAssessmentData(assessmentData);
      
      // Notify parent component
      onComplete(assessmentData, calibrationSettings);
      
      actions.addNotification('Assessment complete! Your device is being configured.', 'success');
    } catch (error) {
      console.error('Failed to complete assessment:', error);
      actions.addError('Failed to complete assessment. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getStrokeTimelineMonths = (timeline) => {
    switch (timeline) {
      case 'recent':
        return 2; // Less than 3 months, average 2 months
      case 'moderate':
        return 7; // 3-12 months, average 7 months
      case 'extended':
        return 18; // 1-2 years, average 18 months
      case 'chronic':
        return 36; // More than 2 years, average 36 months
      default:
        return null;
    }
  };

  const generateCalibrationSettings = (data) => {
    // Generate patient-specific calibration settings based on assessment
    let warningThreshold = 8.0; // Default warning threshold in degrees
    let dangerThreshold = 15.0; // Default danger threshold in degrees
    
    // Adjust thresholds based on severity level
    if (data.severityLevel) {
      switch (data.severityLevel) {
        case 1:
        case 2:
          warningThreshold = 6.0;
          dangerThreshold = 12.0;
          break;
        case 3:
          warningThreshold = 8.0;
          dangerThreshold = 15.0;
          break;
        case 4:
        case 5:
          warningThreshold = 10.0;
          dangerThreshold = 18.0;
          break;
        default:
          break;
      }
    }
    
    // Adjust based on mobility level
    if (data.mobilityLevel) {
      switch (data.mobilityLevel) {
        case 'wheelchair':
          warningThreshold *= 0.8; // More sensitive for wheelchair users
          dangerThreshold *= 0.8;
          break;
        case 'walker':
          warningThreshold *= 0.9;
          dangerThreshold *= 0.9;
          break;
        case 'cane':
          // Keep default values
          break;
        case 'independent':
          warningThreshold *= 1.1; // Less sensitive for independent users
          dangerThreshold *= 1.1;
          break;
        default:
          break;
      }
    }
    
    return {
      baselinePitch: 0.0,
      baselineRoll: 0.0,
      warningThreshold: Math.round(warningThreshold * 10) / 10,
      dangerThreshold: Math.round(dangerThreshold * 10) / 10,
      strokeSide: data.strokeSide,
      severityLevel: data.severityLevel,
      mobilityLevel: data.mobilityLevel
    };
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return true; // Welcome step is always valid
      case 2:
        return assessmentData.strokeSide !== null;
      case 3:
        return assessmentData.severityLevel !== null;
      case 4:
        return assessmentData.mobilityLevel !== null;
      case 5:
        return assessmentData.strokeTimeline !== null && assessmentData.therapyStatus !== null;
      default:
        return false;
    }
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return <WelcomeStep />;
      case 2:
        return (
          <StrokeSideStep
            value={assessmentData.strokeSide}
            onChange={(value) => updateAssessmentData('strokeSide', value)}
          />
        );
      case 3:
        return (
          <SeverityStep
            value={assessmentData.severityLevel}
            onChange={(value) => updateAssessmentData('severityLevel', value)}
          />
        );
      case 4:
        return (
          <MobilityStep
            value={assessmentData.mobilityLevel}
            onChange={(value) => updateAssessmentData('mobilityLevel', value)}
          />
        );
      case 5:
        return (
          <TimelineStep
            strokeTimeline={assessmentData.strokeTimeline}
            therapyStatus={assessmentData.therapyStatus}
            onStrokeTimelineChange={(value) => updateAssessmentData('strokeTimeline', value)}
            onTherapyStatusChange={(value) => updateAssessmentData('therapyStatus', value)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--primary-blue-50)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--spacing-4)'
    }}>
      <div className="container" style={{ maxWidth: '500px' }}>
        <div className="card">
          {/* Header */}
          <div style={{ marginBottom: 'var(--spacing-6)' }}>
            <h1 style={{
              fontSize: 'var(--font-size-xl)',
              fontWeight: '600',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)',
              textAlign: 'center'
            }}>
              Getting Started
            </h1>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              textAlign: 'center',
              marginBottom: 'var(--spacing-4)'
            }}>
              Step {currentStep} of {totalSteps}
            </p>
            
            {/* Progress Bar */}
            <ProgressBar 
              current={currentStep} 
              total={totalSteps} 
              color="var(--primary-blue)"
            />
          </div>

          {/* Step Content */}
          <div style={{ marginBottom: 'var(--spacing-8)' }}>
            {renderCurrentStep()}
          </div>

          {/* Navigation Buttons */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleBack}
              disabled={currentStep === 1 || loading}
              style={{
                visibility: currentStep === 1 ? 'hidden' : 'visible'
              }}
            >
              Back
            </button>

            <button
              type="button"
              className="btn btn-primary"
              onClick={handleNext}
              disabled={!isStepValid() || loading}
              style={{
                opacity: (!isStepValid() || loading) ? 0.6 : 1
              }}
            >
              {loading ? 'Processing...' : (currentStep === totalSteps ? 'Continue' : 'Next')}
            </button>
          </div>

          {/* Step Indicator Dots */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginTop: 'var(--spacing-6)',
            gap: 'var(--spacing-2)'
          }}>
            {Array.from({ length: totalSteps }, (_, index) => (
              <div
                key={index}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: index + 1 <= currentStep ? 'var(--primary-blue)' : 'var(--gray-300)',
                  transition: 'var(--transition-fast)'
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingWizard;