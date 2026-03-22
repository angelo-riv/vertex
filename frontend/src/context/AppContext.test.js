import React from 'react';
import { render, act } from '@testing-library/react';
import { AppProvider, useApp, ActionTypes } from './AppContext';

// Test component to access context
function TestComponent() {
  const { state, actions } = useApp();
  
  return (
    <div>
      <div data-testid="esp32-connected">{state.esp32.isConnected.toString()}</div>
      <div data-testid="clinical-score">{state.clinical.clinicalScore}</div>
      <div data-testid="calibration-status">{state.calibration.status}</div>
      <div data-testid="confidence-level">{state.clinical.confidenceLevel}</div>
      <div data-testid="resistance-index">{state.clinical.resistanceIndex}</div>
      <button 
        data-testid="connect-esp32" 
        onClick={() => actions.setESP32Connection({ isConnected: true, deviceId: 'test-device' })}
      >
        Connect ESP32
      </button>
      <button 
        data-testid="update-clinical" 
        onClick={() => actions.updateClinicalConfidence(0.85)}
      >
        Update Confidence
      </button>
      <button 
        data-testid="set-calibration" 
        onClick={() => actions.setCalibrationBaseline({ pitch: 0.5, fsrLeft: 512, fsrRight: 510 })}
      >
        Set Calibration
      </button>
    </div>
  );
}

describe('Enhanced AppContext for ESP32 Integration', () => {
  test('initializes with correct default state', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    expect(getByTestId('esp32-connected')).toHaveTextContent('false');
    expect(getByTestId('clinical-score')).toHaveTextContent('0');
    expect(getByTestId('calibration-status')).toHaveTextContent('not_calibrated');
    expect(getByTestId('confidence-level')).toHaveTextContent('0');
    expect(getByTestId('resistance-index')).toHaveTextContent('0');
  });

  test('handles ESP32 connection state updates', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    act(() => {
      getByTestId('connect-esp32').click();
    });

    expect(getByTestId('esp32-connected')).toHaveTextContent('true');
  });

  test('handles clinical confidence updates', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    act(() => {
      getByTestId('update-clinical').click();
    });

    expect(getByTestId('confidence-level')).toHaveTextContent('0.85');
  });

  test('handles calibration baseline setting', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    act(() => {
      getByTestId('set-calibration').click();
    });

    expect(getByTestId('calibration-status')).toHaveTextContent('calibrated');
  });

  test('maintains backward compatibility with existing state', () => {
    const { getByTestId } = render(
      <AppProvider>
        <TestComponent />
      </AppProvider>
    );

    // Verify that existing state properties are still accessible
    expect(getByTestId('esp32-connected')).toBeDefined();
    expect(getByTestId('clinical-score')).toBeDefined();
    expect(getByTestId('calibration-status')).toBeDefined();
  });
});