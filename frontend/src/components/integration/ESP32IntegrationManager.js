import React, { useEffect, useState } from 'react';
import { useApp } from '../../context/AppContext';
import ESP32NotificationManager from '../monitoring/ESP32NotificationManager';
import ThresholdConfiguration from '../clinical/ThresholdConfiguration';
import AlertMessage from '../monitoring/AlertMessage';
import axios from 'axios';

/**
 * ESP32 Integration Manager
 * 
 * Central component that integrates ESP32 features with existing Vertex systems.
 * Manages authentication, alerts, clinical thresholds, and device assignments.
 * 
 * Requirements: 19.5, 19.6 - Integration with existing alert and authentication systems
 */
const ESP32IntegrationManager = ({ 
  children,
  showNotifications = true,
  showThresholdConfig = false,
  patientId = null 
}) => {
  const { state, actions } = useApp();
  const [deviceAssignments, setDeviceAssignments] = useState([]);
  const [permissionStatus, setPermissionStatus] = useState({
    canConfigureThresholds: false,
    canManageDevices: false,
    canViewClinicalData: false,
    userRole: 'patient'
  });
  const [integrationStatus, setIntegrationStatus] = useState({
    esp32Connected: false,
    alertsEnabled: true,
    thresholdsConfigured: false,
    calibrationComplete: false
  });

  // Check user permissions on mount and user changes
  useEffect(() => {
    checkUserPermissions();
  }, [state.user]);

  // Monitor ESP32 integration status
  useEffect(() => {
    updateIntegrationStatus();
  }, [
    state.esp32.isConnected,
    state.clinical.thresholds,
    state.calibration.status,
    state.ui.esp32Alerts
  ]);

  // Load device assignments for clinical staff
  useEffect(() => {
    if (permissionStatus.canManageDevices) {
      loadDeviceAssignments();
    }
  }, [permissionStatus.canManageDevices]);

  // Check user permissions based on role
  const checkUserPermissions = async () => {
    try {
      if (!state.user) {
        setPermissionStatus({
          canConfigureThresholds: false,
          canManageDevices: false,
          canViewClinicalData: false,
          userRole: 'anonymous'
        });
        return;
      }

      // Extract user role from authentication context
      const userRole = state.user.user_metadata?.role || 
                      state.user.role || 
                      state.user.app_metadata?.role || 
                      'patient';

      const permissions = {
        canConfigureThresholds: ['therapist', 'clinician', 'admin'].includes(userRole),
        canManageDevices: ['therapist', 'admin'].includes(userRole),
        canViewClinicalData: ['therapist', 'clinician', 'admin'].includes(userRole),
        userRole: userRole
      };

      setPermissionStatus(permissions);

      // Log permission check for security audit
      console.log(`ESP32 Integration: User ${state.user.email} has role ${userRole}`, permissions);

    } catch (error) {
      console.error('Failed to check user permissions:', error);
      setPermissionStatus({
        canConfigureThresholds: false,
        canManageDevices: false,
        canViewClinicalData: false,
        userRole: 'unknown'
      });
    }
  };

  // Update integration status based on current state
  const updateIntegrationStatus = () => {
    const status = {
      esp32Connected: state.esp32.isConnected,
      alertsEnabled: state.ui.esp32Alerts.connectionAlerts || 
                    state.ui.esp32Alerts.pusherAlerts || 
                    state.ui.esp32Alerts.calibrationReminders || 
                    state.ui.esp32Alerts.thresholdAlerts,
      thresholdsConfigured: state.clinical.thresholds.normal !== 5.0 || 
                           state.clinical.thresholds.pusher !== 10.0 || 
                           state.clinical.thresholds.severe !== 20.0,
      calibrationComplete: state.calibration.status === 'calibrated'
    };

    setIntegrationStatus(status);
  };

  // Load ESP32 device assignments (for clinical staff)
  const loadDeviceAssignments = async () => {
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/clinical/devices`,
        {
          headers: {
            'Authorization': `Bearer ${state.user?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data?.devices) {
        setDeviceAssignments(response.data.devices);
      }
    } catch (error) {
      console.error('Failed to load device assignments:', error);
      if (error.response?.status === 403) {
        actions.addNotification('Access denied: Clinical permissions required', 'error');
      }
    }
  };

  // Assign ESP32 device to patient (therapist only)
  const assignDevice = async (deviceId, patientId) => {
    if (!permissionStatus.canManageDevices) {
      actions.addNotification('Access denied: Therapist role required', 'error');
      return false;
    }

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/clinical/devices/${deviceId}/assign`,
        { patient_id: patientId },
        {
          headers: {
            'Authorization': `Bearer ${state.user?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data?.success) {
        actions.addNotification(
          `Device ${deviceId} assigned to patient successfully`,
          'success'
        );
        await loadDeviceAssignments(); // Refresh assignments
        return true;
      }
    } catch (error) {
      console.error('Failed to assign device:', error);
      actions.addNotification('Failed to assign device', 'error');
      return false;
    }
  };

  // Update ESP32 alert preferences
  const updateAlertPreferences = async (preferences) => {
    try {
      const currentPatientId = patientId || state.user?.id;
      if (!currentPatientId) {
        actions.addNotification('Patient ID required for alert preferences', 'error');
        return;
      }

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/clinical/alert-preferences`,
        {
          patient_id: currentPatientId,
          ...preferences
        },
        {
          headers: {
            'Authorization': `Bearer ${state.user?.access_token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.data?.success) {
        // Update local state
        actions.setESP32AlertPreferences(preferences);
        actions.addNotification('Alert preferences updated successfully', 'success');
      }
    } catch (error) {
      console.error('Failed to update alert preferences:', error);
      actions.addNotification('Failed to update alert preferences', 'error');
    }
  };

  // Integration status display component
  const IntegrationStatusDisplay = () => (
    <div style={{
      backgroundColor: 'white',
      borderRadius: 'var(--border-radius-lg)',
      padding: 'var(--spacing-4)',
      marginBottom: 'var(--spacing-4)',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
    }}>
      <h3 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-3)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-2)'
      }}>
        <span style={{ fontSize: 'var(--font-size-lg)' }}>🔗</span>
        ESP32 Integration Status
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 'var(--spacing-3)'
      }}>
        <StatusItem
          label="Device Connection"
          status={integrationStatus.esp32Connected}
          icon="📡"
        />
        <StatusItem
          label="Alerts Enabled"
          status={integrationStatus.alertsEnabled}
          icon="🔔"
        />
        <StatusItem
          label="Thresholds Configured"
          status={integrationStatus.thresholdsConfigured}
          icon="⚙️"
        />
        <StatusItem
          label="Calibration Complete"
          status={integrationStatus.calibrationComplete}
          icon="🎯"
        />
      </div>

      {/* User role and permissions display */}
      <div style={{
        marginTop: 'var(--spacing-4)',
        padding: 'var(--spacing-3)',
        backgroundColor: 'var(--gray-50)',
        borderRadius: 'var(--border-radius-md)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            fontWeight: '500',
            color: 'var(--gray-700)'
          }}>
            User Role: {permissionStatus.userRole}
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--gray-500)'
          }}>
            {permissionStatus.canConfigureThresholds ? 'Clinical access enabled' : 'Patient access only'}
          </div>
        </div>
        
        {permissionStatus.canManageDevices && (
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--primary-blue)',
            fontWeight: '500'
          }}>
            Device Management Available
          </div>
        )}
      </div>
    </div>
  );

  // Status item component
  const StatusItem = ({ label, status, icon }) => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--spacing-2)',
      padding: 'var(--spacing-2)',
      backgroundColor: status ? '#f0fdf4' : '#fef2f2',
      borderRadius: 'var(--border-radius-md)',
      border: `1px solid ${status ? '#bbf7d0' : '#fecaca'}`
    }}>
      <span style={{ fontSize: 'var(--font-size-base)' }}>{icon}</span>
      <div>
        <div style={{
          fontSize: 'var(--font-size-sm)',
          fontWeight: '500',
          color: status ? '#166534' : '#dc2626'
        }}>
          {label}
        </div>
        <div style={{
          fontSize: 'var(--font-size-xs)',
          color: status ? '#15803d' : '#991b1b'
        }}>
          {status ? 'Active' : 'Inactive'}
        </div>
      </div>
    </div>
  );

  // Alert preferences control component
  const AlertPreferencesControl = () => (
    <div style={{
      backgroundColor: 'white',
      borderRadius: 'var(--border-radius-lg)',
      padding: 'var(--spacing-4)',
      marginBottom: 'var(--spacing-4)',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
    }}>
      <h3 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-3)'
      }}>
        Alert Preferences
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 'var(--spacing-3)'
      }}>
        {Object.entries({
          connectionAlerts: 'Connection Alerts',
          pusherAlerts: 'Pusher Detection',
          calibrationReminders: 'Calibration Reminders',
          thresholdAlerts: 'Threshold Alerts'
        }).map(([key, label]) => (
          <label key={key} style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)',
            cursor: 'pointer'
          }}>
            <input
              type="checkbox"
              checked={state.ui.esp32Alerts[key]}
              onChange={(e) => {
                actions.toggleESP32AlertType(key);
                updateAlertPreferences({
                  [key]: e.target.checked
                });
              }}
              style={{
                width: '16px',
                height: '16px'
              }}
            />
            <span style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-700)'
            }}>
              {label}
            </span>
          </label>
        ))}
      </div>

      <div style={{
        marginTop: 'var(--spacing-3)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--spacing-3)'
      }}>
        <label style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--gray-700)',
          fontWeight: '500'
        }}>
          Alert Volume:
        </label>
        <select
          value={state.ui.esp32Alerts.alertVolume}
          onChange={(e) => {
            actions.setAlertVolume(e.target.value);
            updateAlertPreferences({
              alert_volume: e.target.value
            });
          }}
          style={{
            padding: 'var(--spacing-2)',
            border: '1px solid var(--gray-300)',
            borderRadius: 'var(--border-radius-md)',
            fontSize: 'var(--font-size-sm)'
          }}
        >
          <option value="muted">Muted</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
  );

  return (
    <div>
      {/* Integration Status Display */}
      <IntegrationStatusDisplay />

      {/* Alert Preferences Control */}
      <AlertPreferencesControl />

      {/* Threshold Configuration (for therapists) */}
      {showThresholdConfig && permissionStatus.canConfigureThresholds && (
        <ThresholdConfiguration
          patientId={patientId}
          onSave={(thresholds) => {
            actions.setClinicalThresholds(thresholds);
            actions.addNotification('Clinical thresholds updated successfully', 'success');
          }}
          onCancel={() => {
            // Handle cancel if needed
          }}
        />
      )}

      {/* Access Denied Message for Threshold Configuration */}
      {showThresholdConfig && !permissionStatus.canConfigureThresholds && (
        <AlertMessage
          alertLevel="warning"
          message="Therapist role required for clinical threshold configuration. Contact your administrator for access."
          autoHide={false}
        />
      )}

      {/* ESP32 Notification Manager */}
      {showNotifications && (
        <ESP32NotificationManager />
      )}

      {/* Child components */}
      {children}
    </div>
  );
};

export default ESP32IntegrationManager;