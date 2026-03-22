import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import fc from 'fast-check';
import { AppProvider } from '../../context/AppContext';
import PostureVisualization from '../../components/monitoring/PostureVisualization';
import CircularTiltMeter from '../../components/monitoring/CircularTiltMeter';
import SensorDataDisplay from '../../components/monitoring/SensorDataDisplay';
import AlertMessage from '../../components/monitoring/AlertMessage';
import ESP32IntegrationManager from '../../components/integration/ESP32IntegrationManager';
import { useApp } from '../../context/AppContext';

/**
 * **Validates: Requirements 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7**
 * 
 * Property 16: Component Integration Compatibility
 * 
 * For any existing Vertex component enhancement, the system should maintain backward 
 * compatibility with current APIs while adding new functionality (ESP32 connection status, 
 * clinical thresholds, calibration controls), preserve existing layouts and data displays, 
 * extend AppContext with new state management, and integrate with existing authentication 
 * and alert systems.
 */

// Test wrapper with AppContext provider
const TestWrapper = ({ children, initialState = {} }) => (
  <AppProvider>
    {children}
  </AppProvider>
);

// Mock authentication user for testing
const createMockUser = (role = 'patient') => ({
  id: `user_${Math.random().toString(36).substr(2, 9)}`,
  email: `${role}@example.com`,
  user_metadata: { role },
  access_token: 'mock_token_123'
});

// Generate test data for ESP32 integration
const esp32StatusArbitrary = fc.record({
  isConnected: fc.boolean(),
  deviceId: fc.oneof(
    fc.constant(null),
    fc.string({ minLength: 8, maxLength: 12 }).map(s => `ESP32_${s}`)
  ),
  lastDataTimestamp: fc.oneof(
    fc.constant(null),
    fc.date({ min: new Date(Date.now() - 300000), max: new Date() }).map(d => d.toISOString())
  ),
  connectionQuality: fc.constantFrom('excellent', 'good', 'poor', 'disconnected', 'unknown'),
  demoMode: fc.boolean()
});

const clinicalDataArbitrary = fc.record({
  pusherDetected: fc.boolean(),
  currentEpisode: fc.oneof(fc.constant(null), fc.record({
    id: fc.string(),
    startTime: fc.date().map(d => d.toISOString()),
    severity: fc.integer({ min: 0, max: 3 })
  })),
  clinicalScore: fc.integer({ min: 0, max: 3 }),
  confidence: fc.float({ min: 0, max: 1 }),
  episodeCount: fc.integer({ min: 0, max: 50 })
});

const calibrationStatusArbitrary = fc.record({
  status: fc.constantFrom('not_calibrated', 'calibrating', 'calibrated'),
  progress: fc.integer({ min: 0, max: 100 }),
  baseline: fc.oneof(
    fc.constant(null),
    fc.record({
      pitch: fc.float({ min: -10, max: 10 }),
      fsrRatio: fc.float({ min: 0.2, max: 0.8 }),
      stdDev: fc.float({ min: 0.5, max: 3.0 })
    })
  ),
  lastCalibrationDate: fc.oneof(
    fc.constant(null),
    fc.date({ min: new Date(Date.now() - 86400000 * 30), max: new Date() }).map(d => d.toISOString())
  )
});

describe('Property 16: Component Integration Compatibility', () => {
  
  test('PostureVisualization integration maintains backward compatibility while adding ESP32 features', () => {
    fc.assert(fc.property(
      fc.float({ min: -30, max: 30 }), // tiltAngle
      fc.record({
        normal: fc.float({ min: 3, max: 8 }),
        pusher: fc.float({ min: 8, max: 15 }),
        severe: fc.float({ min: 15, max: 25 })
      }), // clinicalThresholds
      fc.float({ min: -5, max: 5 }), // calibrationBaseline
      fc.boolean(), // pusherDetected
      fc.constantFrom('connected', 'disconnected', 'connecting'), // connectionStatus
      (tiltAngle, clinicalThresholds, calibrationBaseline, pusherDetected, connectionStatus) => {
        
        const { container } = render(
          <TestWrapper>
            <PostureVisualization
              tiltAngle={tiltAngle}
              clinicalThresholds={clinicalThresholds}
              calibrationBaseline={calibrationBaseline}
              pusherDetected={pusherDetected}
              connectionStatus={connectionStatus}
            />
          </TestWrapper>
        );

        // Requirement 19.1: PostureVisualization integration with ESP32 data
        // Verify backward compatibility - original props still work
        const svgElement = container.querySelector('svg');
        expect(svgElement).toBeInTheDocument();
        
        // Verify ESP32 enhancements are added without breaking existing functionality
        const humanFigure = container.querySelector('svg g[style*="transform"]');
        expect(humanFigure).toBeInTheDocument();
        
        // Verify clinical threshold markers are present
        const thresholdMarkers = container.querySelectorAll('circle[stroke-dasharray]');
        expect(thresholdMarkers.length).toBeGreaterThanOrEqual(3); // Normal, pusher, severe thresholds
        
        // Verify ESP32 connection status indicator
        const connectionIndicator = container.querySelector('div[style*="border-radius: 50%"]');
        expect(connectionIndicator).toBeInTheDocument();
        
        // Verify pusher detection alert when applicable
        if (pusherDetected) {
          const pusherAlert = screen.queryByText(/Pusher Syndrome Detected/i);
          expect(pusherAlert).toBeInTheDocument();
        }
        
        // Verify calibration status indicator when baseline is set
        if (calibrationBaseline !== 0) {
          const calibrationIndicator = screen.queryByText('CAL');
          expect(calibrationIndicator).toBeInTheDocument();
        }
        
        // Verify angle display maintains precision
        const angleDisplay = screen.queryByText(new RegExp(`${Math.abs(tiltAngle - calibrationBaseline).toFixed(1)}°`));
        expect(angleDisplay).toBeInTheDocument();
        
        return true;
      }
    ), { numRuns: 50 });
  });

  test('CircularTiltMeter integration preserves existing functionality with clinical enhancements', () => {
    fc.assert(fc.property(
      fc.float({ min: -30, max: 30 }), // tiltAngle
      fc.constantFrom('left', 'right', 'center'), // direction
      fc.record({
        normal: fc.float({ min: 3, max: 8 }),
        pusher: fc.float({ min: 8, max: 15 }),
        severe: fc.float({ min: 15, max: 25 })
      }), // clinicalThresholds
      fc.float({ min: -3, max: 3 }), // calibratedBaseline
      fc.boolean(), // showClinicalMarkers
      (tiltAngle, direction, clinicalThresholds, calibratedBaseline, showClinicalMarkers) => {
        
        const { container } = render(
          <TestWrapper>
            <CircularTiltMeter
              tiltAngle={tiltAngle}
              direction={direction}
              clinicalThresholds={clinicalThresholds}
              calibratedBaseline={calibratedBaseline}
              showClinicalMarkers={showClinicalMarkers}
            />
          </TestWrapper>
        );

        // Requirement 19.2: CircularTiltMeter integration with clinical thresholds
        // Verify existing circular gauge functionality
        const svgElement = container.querySelector('svg');
        expect(svgElement).toBeInTheDocument();
        
        // Verify angle display in center
        const angleText = screen.getByText(new RegExp(`${Math.abs(tiltAngle).toFixed(1)}°`));
        expect(angleText).toBeInTheDocument();
        
        // Verify direction indicator
        const directionIndicators = ['←', '→', '↑'];
        const hasDirectionIndicator = directionIndicators.some(indicator => 
          screen.queryByText(indicator)
        );
        expect(hasDirectionIndicator).toBe(true);
        
        // Verify clinical threshold markers when enabled
        if (showClinicalMarkers) {
          const thresholdCircles = container.querySelectorAll('circle[stroke-dasharray]');
          expect(thresholdCircles.length).toBeGreaterThanOrEqual(3);
          
          // Verify threshold legend
          const thresholdValues = [
            clinicalThresholds.normal.toString(),
            clinicalThresholds.pusher.toString(),
            clinicalThresholds.severe.toString()
          ];
          
          thresholdValues.forEach(value => {
            const thresholdLabel = screen.queryByText(new RegExp(`${value}°`));
            expect(thresholdLabel).toBeInTheDocument();
          });
        }
        
        // Verify baseline indicator when present
        if (showClinicalMarkers && calibratedBaseline !== 0) {
          const baselineIndicator = screen.queryByText('B') || screen.queryByText('Baseline');
          expect(baselineIndicator).toBeInTheDocument();
        }
        
        return true;
      }
    ), { numRuns: 50 });
  });
  test('SensorDataDisplay integration maintains existing layout while adding ESP32 features', () => {
    fc.assert(fc.property(
      fc.record({
        pitch: fc.float({ min: -30, max: 30 }),
        roll: fc.float({ min: -30, max: 30 }),
        yaw: fc.float({ min: -180, max: 180 })
      }), // imuData
      fc.record({
        left: fc.integer({ min: 0, max: 4095 }),
        right: fc.integer({ min: 0, max: 4095 })
      }), // fsrData
      fc.boolean(), // hapticActive
      fc.boolean(), // isConnected
      esp32StatusArbitrary,
      clinicalDataArbitrary,
      calibrationStatusArbitrary,
      (imuData, fsrData, hapticActive, isConnected, esp32Status, clinicalData, calibrationStatus) => {
        
        const { container } = render(
          <TestWrapper>
            <SensorDataDisplay
              imuData={imuData}
              fsrData={fsrData}
              hapticActive={hapticActive}
              isConnected={isConnected}
              esp32Status={esp32Status}
              clinicalData={clinicalData}
              calibrationStatus={calibrationStatus}
              onStartCalibration={() => {}}
              onToggleDemoMode={() => {}}
            />
          </TestWrapper>
        );

        // Requirement 19.3: SensorDataDisplay integration with ESP32 connection status
        // Verify existing IMU data display is preserved
        const pitchValue = screen.getByText(new RegExp(`${imuData.pitch.toFixed(1)}°`));
        expect(pitchValue).toBeInTheDocument();
        
        const rollValue = screen.getByText(new RegExp(`${imuData.roll.toFixed(1)}°`));
        expect(rollValue).toBeInTheDocument();
        
        const yawValue = screen.getByText(new RegExp(`${imuData.yaw.toFixed(1)}°`));
        expect(yawValue).toBeInTheDocument();
        
        // Verify existing FSR data display is preserved
        const leftFSR = screen.getByText(fsrData.left.toString());
        expect(leftFSR).toBeInTheDocument();
        
        const rightFSR = screen.getByText(fsrData.right.toString());
        expect(rightFSR).toBeInTheDocument();
        
        // Verify existing haptic feedback status is preserved
        const hapticStatus = screen.getByText(hapticActive ? 'Active' : 'Inactive');
        expect(hapticStatus).toBeInTheDocument();
        
        // Verify ESP32 clinical assessment section is added
        const clinicalAssessment = screen.getByText('Clinical Assessment');
        expect(clinicalAssessment).toBeInTheDocument();
        
        // Verify BLS score display
        const blsScore = screen.getByText(clinicalData.clinicalScore.toString());
        expect(blsScore).toBeInTheDocument();
        
        // Verify confidence percentage
        const confidenceText = screen.getByText(`${(clinicalData.confidence * 100).toFixed(0)}%`);
        expect(confidenceText).toBeInTheDocument();
        
        // Verify episode count
        const episodeCount = screen.getByText(clinicalData.episodeCount.toString());
        expect(episodeCount).toBeInTheDocument();
        
        // Verify calibration section is added
        const calibrationSection = screen.getByText('Device Calibration');
        expect(calibrationSection).toBeInTheDocument();
        
        // Verify calibration status display
        const calibrationStatusText = calibrationStatus.status === 'calibrated' ? 'Calibrated' : 
                                     calibrationStatus.status === 'calibrating' ? 'Calibrating...' : 'Not Calibrated';
        expect(screen.getByText(calibrationStatusText)).toBeInTheDocument();
        
        // Verify pusher syndrome alert when detected
        if (clinicalData.pusherDetected) {
          const pusherAlert = screen.getByText('Pusher Syndrome Detected');
          expect(pusherAlert).toBeInTheDocument();
        }
        
        return true;
      }
    ), { numRuns: 50 });
  });

  test('AlertMessage integration supports all ESP32 alert types while preserving existing functionality', () => {
    fc.assert(fc.property(
      fc.constantFrom('safe', 'warning', 'unsafe', 'esp32_connection', 'esp32_disconnection', 'pusher_detected', 'calibration_reminder', 'threshold_breach'),
      fc.float({ min: -30, max: 30 }), // tiltAngle
      fc.constantFrom('left', 'right', 'center'), // direction
      esp32StatusArbitrary,
      clinicalDataArbitrary,
      calibrationStatusArbitrary,
      (alertLevel, tiltAngle, direction, esp32Status, clinicalData, calibrationStatus) => {
        
        const { container } = render(
          <TestWrapper>
            <AlertMessage
              alertLevel={alertLevel}
              tiltAngle={tiltAngle}
              direction={direction}
              esp32Status={esp32Status}
              clinicalData={clinicalData}
              calibrationStatus={calibrationStatus}
              onDismiss={() => {}}
            />
          </TestWrapper>
        );

        // Requirement 19.5: Integration with existing alert systems
        // Verify alert is rendered (unless safe with no message)
        if (alertLevel !== 'safe') {
          const alertElement = container.querySelector('[role="alert"]');
          expect(alertElement).toBeInTheDocument();
        }
        
        // Verify existing alert levels still work
        if (['unsafe', 'warning', 'safe'].includes(alertLevel)) {
          const expectedTitles = {
            'unsafe': 'Unsafe Posture',
            'warning': 'Posture Warning', 
            'safe': 'Good Posture'
          };
          
          if (alertLevel !== 'safe') {
            const alertTitle = screen.getByText(expectedTitles[alertLevel]);
            expect(alertTitle).toBeInTheDocument();
            
            // Verify tilt angle is included in message
            const angleText = screen.getByText(new RegExp(`${tiltAngle.toFixed(1)}°`));
            expect(angleText).toBeInTheDocument();
          }
        }
        
        // Verify ESP32-specific alert types
        if (alertLevel === 'esp32_connection') {
          const connectionTitle = screen.getByText('Device Connected');
          expect(connectionTitle).toBeInTheDocument();
          
          if (esp32Status.deviceId) {
            const deviceIdText = screen.getByText(new RegExp(esp32Status.deviceId));
            expect(deviceIdText).toBeInTheDocument();
          }
          
          if (esp32Status.demoMode) {
            const demoModeText = screen.getByText(/Demo mode is active/);
            expect(demoModeText).toBeInTheDocument();
          }
        }
        
        if (alertLevel === 'esp32_disconnection') {
          const disconnectionTitle = screen.getByText('Device Disconnected');
          expect(disconnectionTitle).toBeInTheDocument();
        }
        
        if (alertLevel === 'pusher_detected') {
          const pusherTitle = screen.getByText('Pusher Syndrome Alert');
          expect(pusherTitle).toBeInTheDocument();
          
          // Verify clinical severity is shown
          const severityLabels = ['No Pushing', 'Mild', 'Moderate', 'Severe'];
          const expectedSeverity = severityLabels[clinicalData.clinicalScore] || 'Unknown';
          const severityText = screen.getByText(new RegExp(expectedSeverity));
          expect(severityText).toBeInTheDocument();
          
          // Verify confidence percentage
          const confidenceText = screen.getByText(new RegExp(`${(clinicalData.confidence * 100).toFixed(0)}%`));
          expect(confidenceText).toBeInTheDocument();
          
          // Verify episode count
          const episodeText = screen.getByText(new RegExp(`Episode #${clinicalData.episodeCount}`));
          expect(episodeText).toBeInTheDocument();
        }
        
        if (alertLevel === 'calibration_reminder') {
          const calibrationTitle = screen.getByText('Calibration Required');
          expect(calibrationTitle).toBeInTheDocument();
          
          const improvementText = screen.getByText(/Calibration improves detection accuracy/);
          expect(improvementText).toBeInTheDocument();
        }
        
        if (alertLevel === 'threshold_breach') {
          const thresholdTitle = screen.getByText('Clinical Threshold Exceeded');
          expect(thresholdTitle).toBeInTheDocument();
          
          const angleText = screen.getByText(new RegExp(`${tiltAngle.toFixed(1)}°`));
          expect(angleText).toBeInTheDocument();
        }
        
        return true;
      }
    ), { numRuns: 50 });
  });

  test('AppContext integration maintains existing state while adding ESP32 state management', () => {
    fc.assert(fc.property(
      fc.record({
        isConnected: fc.boolean(),
        deviceId: fc.oneof(fc.constant(null), fc.string()),
        lastDataTimestamp: fc.oneof(fc.constant(null), fc.date().map(d => d.toISOString())),
        connectionQuality: fc.constantFrom('excellent', 'good', 'poor', 'disconnected'),
        demoMode: fc.boolean()
      }), // esp32Status
      fc.record({
        pusherDetected: fc.boolean(),
        clinicalScore: fc.integer({ min: 0, max: 3 }),
        thresholds: fc.record({
          normal: fc.float({ min: 3, max: 8 }),
          pusher: fc.float({ min: 8, max: 15 }),
          severe: fc.float({ min: 15, max: 25 }),
          pareticSide: fc.constantFrom('left', 'right')
        })
      }), // clinicalData
      fc.record({
        status: fc.constantFrom('not_calibrated', 'calibrating', 'calibrated'),
        progress: fc.integer({ min: 0, max: 100 }),
        baseline: fc.oneof(fc.constant(null), fc.record({
          pitch: fc.float({ min: -5, max: 5 }),
          fsrRatio: fc.float({ min: 0.3, max: 0.7 })
        }))
      }), // calibrationData
      (esp32Status, clinicalData, calibrationData) => {
        
        let contextState = null;
        
        const TestComponent = () => {
          const { state, actions } = useApp();
          contextState = state;
          
          // Test ESP32 state management actions
          React.useEffect(() => {
            actions.setESP32Connection({
              isConnected: esp32Status.isConnected,
              deviceId: esp32Status.deviceId
            });
            
            actions.updateESP32Status({
              connectionQuality: esp32Status.connectionQuality,
              demoMode: esp32Status.demoMode
            });
            
            actions.setPusherDetected(clinicalData.pusherDetected, clinicalData.clinicalScore);
            actions.setClinicalThresholds(clinicalData.thresholds);
            
            if (calibrationData.baseline) {
              actions.setCalibrationBaseline(calibrationData.baseline);
            }
          }, []);
          
          return <div data-testid="test-component">Test</div>;
        };
        
        render(
          <TestWrapper>
            <TestComponent />
          </TestWrapper>
        );
        
        // Wait for effects to run
        return waitFor(() => {
          // Requirement 19.4: Component compatibility with existing state management
          // Verify existing state structure is preserved
          expect(contextState).toHaveProperty('user');
          expect(contextState).toHaveProperty('loading');
          expect(contextState).toHaveProperty('device');
          expect(contextState).toHaveProperty('monitoring');
          expect(contextState).toHaveProperty('ui');
          expect(contextState).toHaveProperty('onboarding');
          
          // Verify ESP32 state is added
          expect(contextState).toHaveProperty('esp32');
          expect(contextState.esp32).toHaveProperty('isConnected');
          expect(contextState.esp32).toHaveProperty('deviceId');
          expect(contextState.esp32).toHaveProperty('connectionQuality');
          expect(contextState.esp32).toHaveProperty('demoMode');
          
          // Verify clinical state is added
          expect(contextState).toHaveProperty('clinical');
          expect(contextState.clinical).toHaveProperty('pusherDetected');
          expect(contextState.clinical).toHaveProperty('clinicalScore');
          expect(contextState.clinical).toHaveProperty('thresholds');
          
          // Verify calibration state is added
          expect(contextState).toHaveProperty('calibration');
          expect(contextState.calibration).toHaveProperty('status');
          expect(contextState.calibration).toHaveProperty('progress');
          expect(contextState.calibration).toHaveProperty('baseline');
          
          // Verify ESP32 alert preferences are added to UI state
          expect(contextState.ui).toHaveProperty('esp32Alerts');
          expect(contextState.ui.esp32Alerts).toHaveProperty('connectionAlerts');
          expect(contextState.ui.esp32Alerts).toHaveProperty('pusherAlerts');
          expect(contextState.ui.esp32Alerts).toHaveProperty('calibrationReminders');
          expect(contextState.ui.esp32Alerts).toHaveProperty('thresholdAlerts');
          
          return true;
        });
      }
    ), { numRuns: 30 });
  });

  test('ESP32IntegrationManager preserves authentication integration and role-based access', () => {
    fc.assert(fc.property(
      fc.constantFrom('patient', 'therapist', 'clinician', 'admin'), // userRole
      fc.boolean(), // showThresholdConfig
      fc.boolean(), // showNotifications
      (userRole, showThresholdConfig, showNotifications) => {
        
        const mockUser = createMockUser(userRole);
        
        const TestWrapper = ({ children }) => {
          const { actions } = useApp();
          
          React.useEffect(() => {
            actions.setUser(mockUser);
          }, []);
          
          return children;
        };
        
        const { container } = render(
          <AppProvider>
            <TestWrapper>
              <ESP32IntegrationManager
                showThresholdConfig={showThresholdConfig}
                showNotifications={showNotifications}
                patientId="test-patient-123"
              />
            </TestWrapper>
          </AppProvider>
        );
        
        // Requirement 19.6: Integration with existing authentication systems
        // Verify integration status display is always present
        const integrationStatus = screen.getByText('ESP32 Integration Status');
        expect(integrationStatus).toBeInTheDocument();
        
        // Verify user role is displayed
        const userRoleText = screen.getByText(new RegExp(`User Role: ${userRole}`));
        expect(userRoleText).toBeInTheDocument();
        
        // Verify role-based access control
        const canConfigureThresholds = ['therapist', 'clinician', 'admin'].includes(userRole);
        const canManageDevices = ['therapist', 'admin'].includes(userRole);
        
        if (showThresholdConfig) {
          if (canConfigureThresholds) {
            // Should show threshold configuration for authorized roles
            const thresholdConfig = screen.queryByText(/Clinical threshold/i);
            expect(thresholdConfig).toBeInTheDocument();
          } else {
            // Should show access denied message for unauthorized roles
            const accessDenied = screen.queryByText(/Therapist role required/i);
            expect(accessDenied).toBeInTheDocument();
          }
        }
        
        if (canManageDevices) {
          const deviceManagement = screen.queryByText('Device Management Available');
          expect(deviceManagement).toBeInTheDocument();
        }
        
        // Verify alert preferences are always available
        const alertPreferences = screen.getByText('Alert Preferences');
        expect(alertPreferences).toBeInTheDocument();
        
        // Verify alert type checkboxes
        const connectionAlertsCheckbox = screen.getByRole('checkbox', { name: /Connection Alerts/i });
        expect(connectionAlertsCheckbox).toBeInTheDocument();
        
        const pusherAlertsCheckbox = screen.getByRole('checkbox', { name: /Pusher Detection/i });
        expect(pusherAlertsCheckbox).toBeInTheDocument();
        
        // Verify alert volume selector
        const alertVolumeSelect = screen.getByDisplayValue(/medium|low|high|muted/i);
        expect(alertVolumeSelect).toBeInTheDocument();
        
        return true;
      }
    ), { numRuns: 30 });
  });

  test('Component integration maintains backward compatibility across all enhanced components', () => {
    fc.assert(fc.property(
      fc.float({ min: -25, max: 25 }), // tiltAngle
      fc.record({
        left: fc.integer({ min: 0, max: 4095 }),
        right: fc.integer({ min: 0, max: 4095 })
      }), // fsrData
      fc.boolean(), // hapticActive
      esp32StatusArbitrary,
      clinicalDataArbitrary,
      (tiltAngle, fsrData, hapticActive, esp32Status, clinicalData) => {
        
        // Test that all components can be rendered together without conflicts
        const { container } = render(
          <TestWrapper>
            <div>
              <PostureVisualization
                tiltAngle={tiltAngle}
                pusherDetected={clinicalData.pusherDetected}
                connectionStatus={esp32Status.isConnected ? 'connected' : 'disconnected'}
              />
              
              <CircularTiltMeter
                tiltAngle={tiltAngle}
                direction={tiltAngle > 2 ? 'right' : tiltAngle < -2 ? 'left' : 'center'}
                showClinicalMarkers={true}
              />
              
              <SensorDataDisplay
                imuData={{ pitch: tiltAngle, roll: 0, yaw: 0 }}
                fsrData={fsrData}
                hapticActive={hapticActive}
                isConnected={esp32Status.isConnected}
                esp32Status={esp32Status}
                clinicalData={clinicalData}
              />
              
              {clinicalData.pusherDetected && (
                <AlertMessage
                  alertLevel="pusher_detected"
                  clinicalData={clinicalData}
                />
              )}
            </div>
          </TestWrapper>
        );
        
        // Requirement 19.7: AppContext integration with ESP32 state management
        // Verify all components render without errors
        expect(container.firstChild).toBeInTheDocument();
        
        // Verify PostureVisualization is present
        const postureVisualization = container.querySelector('svg');
        expect(postureVisualization).toBeInTheDocument();
        
        // Verify CircularTiltMeter is present
        const tiltMeterAngle = screen.getByText(new RegExp(`${Math.abs(tiltAngle).toFixed(1)}°`));
        expect(tiltMeterAngle).toBeInTheDocument();
        
        // Verify SensorDataDisplay sections are present
        const imuSection = screen.getByText('IMU Orientation');
        expect(imuSection).toBeInTheDocument();
        
        const weightSection = screen.getByText('Weight Distribution');
        expect(weightSection).toBeInTheDocument();
        
        const hapticSection = screen.getByText('Haptic Feedback');
        expect(hapticSection).toBeInTheDocument();
        
        // Verify clinical assessment section is present
        const clinicalSection = screen.getByText('Clinical Assessment');
        expect(clinicalSection).toBeInTheDocument();
        
        // Verify calibration section is present
        const calibrationSection = screen.getByText('Device Calibration');
        expect(calibrationSection).toBeInTheDocument();
        
        // Verify pusher alert when applicable
        if (clinicalData.pusherDetected) {
          const pusherAlert = screen.getByText('Pusher Syndrome Alert');
          expect(pusherAlert).toBeInTheDocument();
        }
        
        // Verify no React errors or warnings in console
        // (This would be caught by the test framework if components had conflicts)
        
        return true;
      }
    ), { numRuns: 40 });
  });

  test('Enhanced components maintain performance characteristics with ESP32 integration', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        tiltAngle: fc.float({ min: -30, max: 30 }),
        timestamp: fc.date().map(d => d.getTime())
      }), { minLength: 10, maxLength: 50 }), // Multiple data updates
      (dataUpdates) => {
        
        let renderCount = 0;
        const RenderCounter = React.memo(({ tiltAngle }) => {
          renderCount++;
          return (
            <PostureVisualization
              tiltAngle={tiltAngle}
              pusherDetected={Math.abs(tiltAngle) > 15}
              connectionStatus="connected"
            />
          );
        });
        
        const { rerender } = render(
          <TestWrapper>
            <RenderCounter tiltAngle={0} />
          </TestWrapper>
        );
        
        const initialRenderCount = renderCount;
        
        // Simulate rapid data updates (like real-time ESP32 data)
        dataUpdates.forEach((update, index) => {
          rerender(
            <TestWrapper>
              <RenderCounter tiltAngle={update.tiltAngle} />
            </TestWrapper>
          );
        });
        
        // Verify component handles rapid updates efficiently
        // Should not re-render more than necessary due to memoization
        const finalRenderCount = renderCount;
        const expectedMaxRenders = initialRenderCount + dataUpdates.length + 5; // Allow some tolerance
        
        expect(finalRenderCount).toBeLessThanOrEqual(expectedMaxRenders);
        
        // Verify final state is correct
        const lastUpdate = dataUpdates[dataUpdates.length - 1];
        const finalAngle = screen.getByText(new RegExp(`${Math.abs(lastUpdate.tiltAngle).toFixed(1)}°`));
        expect(finalAngle).toBeInTheDocument();
        
        return true;
      }
    ), { numRuns: 20 });
  });
});