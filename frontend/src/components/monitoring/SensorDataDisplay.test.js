import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SensorDataDisplay from './SensorDataDisplay';

describe('SensorDataDisplay', () => {
  const defaultProps = {
    imuData: { pitch: 5.2, roll: -2.1, yaw: 0.8 },
    fsrData: { left: 1200, right: 1800 },
    hapticActive: false,
    isConnected: true
  };

  const esp32Props = {
    esp32Status: {
      isConnected: true,
      deviceId: 'ESP32-001',
      lastDataTimestamp: new Date().toISOString(),
      connectionQuality: 'excellent',
      demoMode: false
    },
    clinicalData: {
      pusherDetected: false,
      currentEpisode: null,
      clinicalScore: 0,
      confidence: 0.85,
      episodeCount: 2
    },
    calibrationStatus: {
      status: 'calibrated',
      progress: 0,
      baseline: {
        pitch: 0.5,
        fsrRatio: 0.6,
        stdDev: 1.2
      },
      lastCalibrationDate: new Date().toISOString()
    }
  };

  test('renders basic sensor data correctly', () => {
    render(<SensorDataDisplay {...defaultProps} />);
    
    expect(screen.getByText('5.2°')).toBeInTheDocument();
    expect(screen.getByText('1200')).toBeInTheDocument();
    expect(screen.getByText('1800')).toBeInTheDocument();
    expect(screen.getByText('ESP32 Connected')).toBeInTheDocument(); // Updated to match new behavior
  });

  test('displays ESP32 connection status', () => {
    render(<SensorDataDisplay {...defaultProps} {...esp32Props} />);
    
    expect(screen.getByText('ESP32 Connected')).toBeInTheDocument();
    expect(screen.getByText('Device: ESP32-001')).toBeInTheDocument();
    expect(screen.getByText('Excellent')).toBeInTheDocument();
  });

  test('shows clinical assessment data', () => {
    render(<SensorDataDisplay {...defaultProps} {...esp32Props} />);
    
    expect(screen.getByText('Clinical Assessment')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // confidence
    expect(screen.getByText('2')).toBeInTheDocument(); // episode count
  });

  test('displays calibration status', () => {
    render(<SensorDataDisplay {...defaultProps} {...esp32Props} />);
    
    expect(screen.getByText('Device Calibration')).toBeInTheDocument();
    expect(screen.getByText('Status: Calibrated')).toBeInTheDocument();
    expect(screen.getByText('0.5°')).toBeInTheDocument(); // baseline pitch
  });

  test('shows pusher syndrome alert when detected', () => {
    const pusherProps = {
      ...esp32Props,
      clinicalData: {
        ...esp32Props.clinicalData,
        pusherDetected: true,
        clinicalScore: 2
      }
    };

    render(<SensorDataDisplay {...defaultProps} {...pusherProps} />);
    
    expect(screen.getByText('Pusher Syndrome Detected')).toBeInTheDocument();
    expect(screen.getByText(/Severity: Moderate/)).toBeInTheDocument();
  });

  test('handles calibration button click', () => {
    const onStartCalibration = jest.fn();
    render(
      <SensorDataDisplay 
        {...defaultProps} 
        {...esp32Props} 
        onStartCalibration={onStartCalibration}
      />
    );
    
    const calibrateButton = screen.getByText('Start Calibration');
    fireEvent.click(calibrateButton);
    
    expect(onStartCalibration).toHaveBeenCalled();
  });

  test('shows demo mode toggle when disconnected', () => {
    const onToggleDemoMode = jest.fn();
    const disconnectedProps = {
      ...esp32Props,
      esp32Status: {
        ...esp32Props.esp32Status,
        isConnected: false
      }
    };

    render(
      <SensorDataDisplay 
        {...defaultProps} 
        {...disconnectedProps}
        isConnected={false}
        onToggleDemoMode={onToggleDemoMode}
      />
    );
    
    const demoButton = screen.getByText('Enable Demo');
    fireEvent.click(demoButton);
    
    expect(onToggleDemoMode).toHaveBeenCalled();
  });

  test('displays calibration progress during calibration', () => {
    const calibratingProps = {
      ...esp32Props,
      calibrationStatus: {
        ...esp32Props.calibrationStatus,
        status: 'calibrating',
        progress: 65
      }
    };

    render(<SensorDataDisplay {...defaultProps} {...calibratingProps} />);
    
    expect(screen.getByText('Calibrating...')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
    expect(screen.getByText('Please maintain normal upright posture during calibration')).toBeInTheDocument();
  });

  test('preserves existing FSR data layout', () => {
    render(<SensorDataDisplay {...defaultProps} {...esp32Props} />);
    
    // Check that FSR section still exists with original structure
    expect(screen.getByText('Weight Distribution')).toBeInTheDocument();
    expect(screen.getByText('Left FSR')).toBeInTheDocument();
    expect(screen.getByText('Right FSR')).toBeInTheDocument();
    expect(screen.getByText('Balance')).toBeInTheDocument();
    
    // Check balance calculation is preserved
    expect(screen.getByText('20% R')).toBeInTheDocument(); // (1800-1200)/(1800+1200) = 0.2 = 20% R
  });

  test('handles disconnected state correctly', () => {
    const disconnectedProps = {
      ...defaultProps,
      isConnected: false,
      esp32Status: {
        ...esp32Props.esp32Status,
        isConnected: false,
        connectionQuality: 'disconnected'
      }
    };

    render(<SensorDataDisplay {...disconnectedProps} />);
    
    expect(screen.getByText('Device Disconnected')).toBeInTheDocument();
    // Check for multiple -- elements (there should be 6 total: 3 IMU + 3 FSR)
    const dashElements = screen.getAllByText('--');
    expect(dashElements).toHaveLength(6);
  });
});