import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import axios from 'axios';

/**
 * Clinical Threshold Configuration Component
 * 
 * Allows therapists to configure patient-specific clinical thresholds
 * for pusher syndrome detection. Requires therapist role permissions.
 * 
 * Requirements: 19.6 - Integration with existing authentication systems
 */
const ThresholdConfiguration = ({ 
  patientId,
  onSave = () => {},
  onCancel = () => {},
  readOnly = false 
}) => {
  const { state, actions } = useApp();
  const [thresholds, setThresholds] = useState({
    normal: 5.0,
    pusher: 10.0,
    severe: 20.0,
    pareticSide: 'right',
    resistanceThreshold: 2.0,
    episodeDurationMin: 2.0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasPermission, setHasPermission] = useState(false);

  // Check user permissions on component mount
  useEffect(() => {
    checkTherapistPermissions();
  }, [state.user]);

  // Load existing thresholds for patient
  useEffect(() => {
    if (patientId && hasPermission) {
      loadPatientThresholds();
    }
  }, [patientId, hasPermission]);

  // Check if user has therapist permissions
  const checkTherapistPermissions = async () => {
    try {
      if (!state.user) {
        setHasPermission(false);
        return;
      }

      // Check user role from authentication context
      const userRole = state.user.user_metadata?.role || state.user.role || 'patient';
      
      if (['therapist', 'clinician', 'admin'].includes(userRole)) {
        setHasPermission(true);
      } else {
        setHasPermission(false);
        setError('Therapist role required for threshold configuration');
      }
    } catch (err) {
      console.error('Permission check failed:', err);
      setHasPermission(false);
      setError('Unable to verify permissions');
    }
  };

  // Load patient-specific thresholds from backend
  const loadPatientThresholds = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/clinical/thresholds/${patientId}`,
        {
          headers: {
            'Authorization': `Bearer ${state.user?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data) {
        setThresholds({
          normal: response.data.normal_threshold || 5.0,
          pusher: response.data.pusher_threshold || 10.0,
          severe: response.data.severe_threshold || 20.0,
          pareticSide: response.data.paretic_side || 'right',
          resistanceThreshold: response.data.resistance_threshold || 2.0,
          episodeDurationMin: response.data.episode_duration_min || 2.0
        });
      }
    } catch (err) {
      console.error('Failed to load thresholds:', err);
      if (err.response?.status === 404) {
        // No existing thresholds, use defaults
        setError(null);
      } else if (err.response?.status === 403) {
        setError('Access denied: Therapist role required');
        setHasPermission(false);
      } else {
        setError('Failed to load patient thresholds');
      }
    } finally {
      setLoading(false);
    }
  };

  // Save threshold configuration
  const saveThresholds = async () => {
    if (!hasPermission || readOnly) return;

    try {
      setLoading(true);
      setError(null);

      const thresholdData = {
        patient_id: patientId,
        paretic_side: thresholds.pareticSide,
        normal_threshold: thresholds.normal,
        pusher_threshold: thresholds.pusher,
        severe_threshold: thresholds.severe,
        resistance_threshold: thresholds.resistanceThreshold,
        episode_duration_min: thresholds.episodeDurationMin,
        created_by: state.user?.id || state.user?.email
      };

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/clinical/thresholds`,
        thresholdData,
        {
          headers: {
            'Authorization': `Bearer ${state.user?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data) {
        // Update local state
        actions.setClinicalThresholds(thresholds);
        
        // Show success notification
        actions.addNotification(
          'Clinical thresholds updated successfully',
          'success'
        );

        onSave(thresholds);
      }
    } catch (err) {
      console.error('Failed to save thresholds:', err);
      if (err.response?.status === 403) {
        setError('Access denied: Therapist role required');
        setHasPermission(false);
      } else {
        setError('Failed to save threshold configuration');
      }
      
      actions.addNotification(
        'Failed to save threshold configuration',
        'error'
      );
    } finally {
      setLoading(false);
    }
  };

  // Handle threshold value changes
  const handleThresholdChange = (field, value) => {
    setThresholds(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Validate threshold values
  const validateThresholds = () => {
    const errors = [];
    
    if (thresholds.normal >= thresholds.pusher) {
      errors.push('Normal threshold must be less than pusher threshold');
    }
    
    if (thresholds.pusher >= thresholds.severe) {
      errors.push('Pusher threshold must be less than severe threshold');
    }
    
    if (thresholds.resistanceThreshold <= 0) {
      errors.push('Resistance threshold must be positive');
    }
    
    if (thresholds.episodeDurationMin <= 0) {
      errors.push('Episode duration must be positive');
    }
    
    return errors;
  };

  const validationErrors = validateThresholds();
  const canSave = hasPermission && !readOnly && validationErrors.length === 0 && !loading;

  // Permission denied view
  if (!hasPermission) {
    return (
      <div style={{
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: 'var(--border-radius-lg)',
        padding: 'var(--spacing-4)',
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: 'var(--font-size-lg)',
          color: '#dc2626',
          marginBottom: 'var(--spacing-2)'
        }}>
          🔒 Access Restricted
        </div>
        <div style={{
          fontSize: 'var(--font-size-base)',
          color: '#991b1b',
          marginBottom: 'var(--spacing-2)'
        }}>
          Therapist Role Required
        </div>
        <div style={{
          fontSize: 'var(--font-size-sm)',
          color: '#7f1d1d'
        }}>
          Clinical threshold configuration requires therapist or clinician permissions.
          Please contact your administrator for access.
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: 'var(--border-radius-lg)',
      padding: 'var(--spacing-6)',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    }}>
      <h2 style={{
        fontSize: 'var(--font-size-xl)',
        fontWeight: '700',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-4)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-2)'
      }}>
        <span style={{ fontSize: 'var(--font-size-lg)' }}>⚙️</span>
        Clinical Threshold Configuration
      </h2>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 'var(--border-radius-md)',
          padding: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-4)',
          color: '#dc2626',
          fontSize: 'var(--font-size-sm)'
        }}>
          {error}
        </div>
      )}

      {validationErrors.length > 0 && (
        <div style={{
          backgroundColor: '#fef3c7',
          border: '1px solid #fcd34d',
          borderRadius: 'var(--border-radius-md)',
          padding: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-4)'
        }}>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: '600',
            color: '#92400e',
            marginBottom: 'var(--spacing-1)'
          }}>
            Validation Errors:
          </div>
          {validationErrors.map((error, index) => (
            <div key={index} style={{
              fontSize: 'var(--font-size-sm)',
              color: '#a16207'
            }}>
              • {error}
            </div>
          ))}
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: 'var(--spacing-6)'
      }}>
        {/* Paretic Side Configuration */}
        <div>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-800)',
            marginBottom: 'var(--spacing-3)'
          }}>
            Patient Assessment
          </h3>
          
          <div style={{ marginBottom: 'var(--spacing-4)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Paretic Side (Affected Side)
            </label>
            <select
              value={thresholds.pareticSide}
              onChange={(e) => handleThresholdChange('pareticSide', e.target.value)}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            >
              <option value="left">Left Side</option>
              <option value="right">Right Side</option>
            </select>
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Side affected by stroke (determines pusher detection direction)
            </div>
          </div>
        </div>

        {/* Angle Thresholds */}
        <div>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-800)',
            marginBottom: 'var(--spacing-3)'
          }}>
            Tilt Angle Thresholds
          </h3>
          
          <div style={{ marginBottom: 'var(--spacing-3)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Normal Threshold (°)
            </label>
            <input
              type="number"
              min="1"
              max="15"
              step="0.5"
              value={thresholds.normal}
              onChange={(e) => handleThresholdChange('normal', parseFloat(e.target.value))}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            />
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Maximum acceptable lean angle (typically 5-7°)
            </div>
          </div>

          <div style={{ marginBottom: 'var(--spacing-3)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Pusher Threshold (°)
            </label>
            <input
              type="number"
              min="5"
              max="25"
              step="0.5"
              value={thresholds.pusher}
              onChange={(e) => handleThresholdChange('pusher', parseFloat(e.target.value))}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            />
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Angle indicating potential pusher syndrome (typically 10°)
            </div>
          </div>

          <div style={{ marginBottom: 'var(--spacing-3)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Severe Threshold (°)
            </label>
            <input
              type="number"
              min="10"
              max="45"
              step="0.5"
              value={thresholds.severe}
              onChange={(e) => handleThresholdChange('severe', parseFloat(e.target.value))}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            />
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Angle indicating severe pusher syndrome (typically 20°)
            </div>
          </div>
        </div>

        {/* Episode Detection Parameters */}
        <div>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-800)',
            marginBottom: 'var(--spacing-3)'
          }}>
            Episode Detection
          </h3>
          
          <div style={{ marginBottom: 'var(--spacing-3)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Resistance Threshold
            </label>
            <input
              type="number"
              min="0.5"
              max="5"
              step="0.1"
              value={thresholds.resistanceThreshold}
              onChange={(e) => handleThresholdChange('resistanceThreshold', parseFloat(e.target.value))}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            />
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Resistance to correction multiplier (typically 2.0)
            </div>
          </div>

          <div style={{ marginBottom: 'var(--spacing-3)' }}>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Minimum Episode Duration (seconds)
            </label>
            <input
              type="number"
              min="0.5"
              max="10"
              step="0.5"
              value={thresholds.episodeDurationMin}
              onChange={(e) => handleThresholdChange('episodeDurationMin', parseFloat(e.target.value))}
              disabled={readOnly || loading}
              style={{
                width: '100%',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--border-radius-md)',
                fontSize: 'var(--font-size-base)',
                backgroundColor: readOnly ? 'var(--gray-100)' : 'white'
              }}
            />
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              marginTop: 'var(--spacing-1)'
            }}>
              Minimum duration to classify as pusher episode (typically 2s)
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {!readOnly && (
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 'var(--spacing-3)',
          marginTop: 'var(--spacing-6)',
          paddingTop: 'var(--spacing-4)',
          borderTop: '1px solid var(--gray-200)'
        }}>
          <button
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: 'var(--spacing-3) var(--spacing-4)',
              backgroundColor: 'white',
              color: 'var(--gray-700)',
              border: '1px solid var(--gray-300)',
              borderRadius: 'var(--border-radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            Cancel
          </button>
          
          <button
            onClick={saveThresholds}
            disabled={!canSave}
            style={{
              padding: 'var(--spacing-3) var(--spacing-4)',
              backgroundColor: canSave ? 'var(--primary-blue)' : 'var(--gray-400)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--border-radius-md)',
              fontSize: 'var(--font-size-base)',
              fontWeight: '500',
              cursor: canSave ? 'pointer' : 'not-allowed',
              opacity: canSave ? 1 : 0.6
            }}
          >
            {loading ? 'Saving...' : 'Save Thresholds'}
          </button>
        </div>
      )}
    </div>
  );
};

export default ThresholdConfiguration;