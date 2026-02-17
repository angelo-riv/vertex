import React, { useState } from 'react';
import { useApp } from '../context/AppContext';

const SettingsPage = () => {
  const { state, actions } = useApp();
  const [feedbackMode, setFeedbackMode] = useState('both');
  const [alertThreshold, setAlertThreshold] = useState(8);
  const [privacySettings, setPrivacySettings] = useState('healthcare_provider');

  const feedbackOptions = [
    { id: 'none', label: 'No Feedback', description: 'Monitor only, no corrections' },
    { id: 'notifications', label: 'Notifications Only', description: 'Visual alerts on phone only' },
    { id: 'haptics', label: 'Haptic Only', description: 'Vibration feedback only' },
    { id: 'both', label: 'Both', description: 'Notifications and haptic feedback' }
  ];

  const privacyOptions = [
    { id: 'healthcare_provider', label: 'Healthcare Provider', description: 'Share with assigned therapist/doctor' },
    { id: 'full_reports', label: 'Full Reports', description: 'Detailed data sharing for research' },
    { id: 'summaries_only', label: 'Summaries Only', description: 'Share progress summaries only' },
    { id: 'private', label: 'Private', description: 'Keep all data private' }
  ];

  const handleSaveSettings = () => {
    // TODO: Implement settings save to backend
    actions.addNotification('Settings saved successfully', 'success');
  };

  const handleStartCalibration = () => {
    // TODO: Implement calibration wizard
    actions.addNotification('Calibration wizard coming soon', 'info');
  };

  const handleExportData = () => {
    // TODO: Implement data export
    actions.addNotification('Data export feature coming soon', 'info');
  };

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '1200px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 160px)' // Account for header and bottom nav
    }}>
      {/* Page Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <h1 style={{
          fontSize: 'var(--font-size-2xl)',
          fontWeight: '700',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-2)',
          letterSpacing: '-0.025em',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-3)'
        }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Device Settings
        </h1>
        <p style={{
          fontSize: 'var(--font-size-lg)',
          color: 'var(--gray-600)',
          lineHeight: '1.6',
          margin: 0
        }}>
          Configure your Vertex rehabilitation device and customize your therapy experience.
        </p>
      </div>

      {/* Main Settings Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
        gap: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Device Settings */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h2 style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-5)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            Device Configuration
          </h2>

          {/* Feedback Mode */}
          <div style={{ marginBottom: 'var(--spacing-6)' }}>
            <h3 style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '600',
              color: 'var(--gray-800)',
              marginBottom: 'var(--spacing-3)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)'
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              Feedback Mode
            </h3>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 'var(--spacing-3)'
            }}>
              {feedbackOptions.map((option) => (
                <label
                  key={option.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    padding: 'var(--spacing-4)',
                    border: `2px solid ${feedbackMode === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: feedbackMode === option.id ? 'var(--primary-blue-50)' : 'white',
                    cursor: 'pointer',
                    transition: 'var(--transition-fast)',
                    minHeight: '80px'
                  }}
                >
                  <input
                    type="radio"
                    name="feedbackMode"
                    value={option.id}
                    checked={feedbackMode === option.id}
                    onChange={(e) => setFeedbackMode(e.target.value)}
                    style={{
                      marginRight: 'var(--spacing-3)',
                      marginTop: '2px',
                      accentColor: 'var(--primary-blue)',
                      transform: 'scale(1.2)'
                    }}
                  />
                  <div>
                    <div style={{
                      fontSize: 'var(--font-size-base)',
                      fontWeight: '600',
                      color: 'var(--gray-900)',
                      marginBottom: 'var(--spacing-1)'
                    }}>
                      {option.label}
                    </div>
                    <div style={{
                      fontSize: 'var(--font-size-sm)',
                      color: 'var(--gray-600)',
                      lineHeight: '1.4'
                    }}>
                      {option.description}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Alert Threshold */}
          <div style={{ marginBottom: 'var(--spacing-6)' }}>
            <h3 style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '600',
              color: 'var(--gray-800)',
              marginBottom: 'var(--spacing-3)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)'
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              Alert Threshold: {alertThreshold}°
            </h3>

            <div style={{
              backgroundColor: 'var(--gray-50)',
              padding: 'var(--spacing-4)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--gray-200)'
            }}>
              <input
                type="range"
                min="5"
                max="20"
                step="1"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  height: '8px',
                  borderRadius: '4px',
                  background: `linear-gradient(to right, var(--primary-blue) 0%, var(--primary-blue) ${((alertThreshold - 5) / 15) * 100}%, var(--gray-200) ${((alertThreshold - 5) / 15) * 100}%, var(--gray-200) 100%)`,
                  outline: 'none',
                  appearance: 'none',
                  cursor: 'pointer',
                  marginBottom: 'var(--spacing-3)'
                }}
              />

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-500)',
                marginBottom: 'var(--spacing-2)'
              }}>
                <span>5° (Sensitive)</span>
                <span>20° (Relaxed)</span>
              </div>

              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                margin: 0,
                lineHeight: '1.5'
              }}>
                Lower values trigger alerts sooner. Adjust based on your comfort and therapy goals.
              </p>
            </div>
          </div>

          {/* Calibration */}
          <div>
            <h3 style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: '600',
              color: 'var(--gray-800)',
              marginBottom: 'var(--spacing-3)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)'
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
              Device Calibration
            </h3>

            <div style={{
              backgroundColor: 'var(--gray-50)',
              padding: 'var(--spacing-4)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--gray-200)',
              marginBottom: 'var(--spacing-3)'
            }}>
              <button
                onClick={handleStartCalibration}
                className="btn btn-primary"
                style={{ 
                  width: '100%',
                  padding: 'var(--spacing-4)',
                  fontSize: 'var(--font-size-base)',
                  fontWeight: '600'
                }}
              >
                Start Calibration Wizard
              </button>
            </div>

            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              margin: 0,
              lineHeight: '1.5'
            }}>
              Recalibrate your device if you notice inaccurate readings or after significant changes in your condition.
            </p>
          </div>
        </div>

        {/* Privacy Settings */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-xl)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-5)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Privacy & Data Sharing
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-3)',
            marginBottom: 'var(--spacing-5)'
          }}>
            {privacyOptions.map((option) => (
              <label
                key={option.id}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  padding: 'var(--spacing-4)',
                  border: `2px solid ${privacySettings === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: privacySettings === option.id ? 'var(--primary-blue-50)' : 'white',
                  cursor: 'pointer',
                  transition: 'var(--transition-fast)',
                  minHeight: '70px'
                }}
              >
                <input
                  type="radio"
                  name="privacySettings"
                  value={option.id}
                  checked={privacySettings === option.id}
                  onChange={(e) => setPrivacySettings(e.target.value)}
                  style={{
                    marginRight: 'var(--spacing-3)',
                    marginTop: '2px',
                    accentColor: 'var(--primary-blue)',
                    transform: 'scale(1.2)'
                  }}
                />
                <div>
                  <div style={{
                    fontSize: 'var(--font-size-base)',
                    fontWeight: '600',
                    color: 'var(--gray-900)',
                    marginBottom: 'var(--spacing-1)'
                  }}>
                    {option.label}
                  </div>
                  <div style={{
                    fontSize: 'var(--font-size-sm)',
                    color: 'var(--gray-600)',
                    lineHeight: '1.4'
                  }}>
                    {option.description}
                  </div>
                </div>
              </label>
            ))}
          </div>

          <button
            onClick={handleExportData}
            className="btn btn-secondary"
            style={{ 
              width: '100%',
              padding: 'var(--spacing-4)',
              fontSize: 'var(--font-size-base)',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 'var(--spacing-2)'
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7,10 12,15 17,10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export My Data
          </button>
        </div>
      </div>

      {/* Save Settings */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)',
        textAlign: 'center'
      }}>
        <button
          onClick={handleSaveSettings}
          className="btn btn-primary"
          style={{ 
            fontSize: 'var(--font-size-lg)',
            fontWeight: '700',
            padding: 'var(--spacing-4) var(--spacing-8)',
            minWidth: '200px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--spacing-2)'
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17,21 17,13 7,13 7,21"/>
            <polyline points="7,3 7,8 15,8"/>
          </svg>
          Save All Settings
        </button>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--gray-600)',
          margin: 'var(--spacing-3) 0 0 0',
          lineHeight: '1.5'
        }}>
          Changes will be applied to your device immediately after saving.
        </p>
      </div>
    </div>
  );
};

export default SettingsPage;