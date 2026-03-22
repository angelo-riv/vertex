/**
 * Tests for WebSocketStatus Component
 * 
 * Tests connection status indicators, color coding, and display formatting.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import WebSocketStatus from './WebSocketStatus';
import { AppProvider } from '../../context/AppContext';
import useWebSocket from '../../hooks/useWebSocket';

// Mock the useWebSocket hook
jest.mock('../../hooks/useWebSocket');

const wrapper = ({ children }) => <AppProvider>{children}</AppProvider>;

describe('WebSocketStatus Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display connected status with green indicator', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    render(<WebSocketStatus />, { wrapper });

    expect(screen.getByText('Connected')).toBeInTheDocument();
    
    // Check for green color indicator (●)
    const statusIcon = screen.getByText('●');
    expect(statusIcon).toBeInTheDocument();
  });

  test('should display connecting status with amber indicator', () => {
    useWebSocket.mockReturnValue({
      isConnected: false,
      connectionStatus: 'connecting',
      reconnectAttempts: 1,
      lastConnectionTime: null,
      lastDataTime: null,
      connectionQuality: 'poor'
    });

    render(<WebSocketStatus />, { wrapper });

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
    
    // Check for connecting indicator (◐)
    const statusIcon = screen.getByText('◐');
    expect(statusIcon).toBeInTheDocument();
  });

  test('should display disconnected status with red indicator', () => {
    useWebSocket.mockReturnValue({
      isConnected: false,
      connectionStatus: 'disconnected',
      reconnectAttempts: 3,
      lastConnectionTime: new Date(Date.now() - 30000), // 30 seconds ago
      lastDataTime: new Date(Date.now() - 30000),
      connectionQuality: 'poor'
    });

    render(<WebSocketStatus />, { wrapper });

    expect(screen.getByText('Disconnected')).toBeInTheDocument();
    
    // Check for red color indicator (●)
    const statusIcon = screen.getByText('●');
    expect(statusIcon).toBeInTheDocument();
  });

  test('should display error status with warning indicator', () => {
    useWebSocket.mockReturnValue({
      isConnected: false,
      connectionStatus: 'error',
      reconnectAttempts: 2,
      lastConnectionTime: null,
      lastDataTime: null,
      connectionQuality: 'poor'
    });

    render(<WebSocketStatus />, { wrapper });

    expect(screen.getByText('Error')).toBeInTheDocument();
    
    // Check for warning indicator (⚠)
    const statusIcon = screen.getByText('⚠');
    expect(statusIcon).toBeInTheDocument();
  });

  test('should show connection quality bars when connected', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    const { container } = render(<WebSocketStatus />, { wrapper });

    // Check for quality indicator bars (should be 3 divs with specific styling)
    const qualityBars = container.querySelectorAll('.w-1.h-3.rounded-sm');
    expect(qualityBars).toHaveLength(3);
  });

  test('should not show connection quality bars when disconnected', () => {
    useWebSocket.mockReturnValue({
      isConnected: false,
      connectionStatus: 'disconnected',
      reconnectAttempts: 1,
      lastConnectionTime: null,
      lastDataTime: null,
      connectionQuality: 'poor'
    });

    const { container } = render(<WebSocketStatus />, { wrapper });

    // Check that quality bars are not present
    const qualityBars = container.querySelectorAll('.w-1.h-3.rounded-sm');
    expect(qualityBars).toHaveLength(0);
  });

  test('should show detailed information when showDetails is true', () => {
    const lastConnectionTime = new Date(Date.now() - 60000); // 1 minute ago
    const lastDataTime = new Date(Date.now() - 30000); // 30 seconds ago

    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime,
      lastDataTime,
      connectionQuality: 'good'
    });

    render(<WebSocketStatus showDetails={true} />, { wrapper });

    expect(screen.getByText('Real-time data streaming active')).toBeInTheDocument();
    expect(screen.getByText(/Connected:/)).toBeInTheDocument();
    expect(screen.getByText(/Last data:/)).toBeInTheDocument();
  });

  test('should not show detailed information when showDetails is false', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    render(<WebSocketStatus showDetails={false} />, { wrapper });

    expect(screen.queryByText('Real-time data streaming active')).not.toBeInTheDocument();
    expect(screen.queryByText(/Connected:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Last data:/)).not.toBeInTheDocument();
  });

  test('should apply small size styling', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    const { container } = render(<WebSocketStatus size="small" />, { wrapper });

    // Check for small size classes
    const statusContainer = container.querySelector('.px-2.py-1.text-xs');
    expect(statusContainer).toBeInTheDocument();
  });

  test('should apply large size styling', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    const { container } = render(<WebSocketStatus size="large" />, { wrapper });

    // Check for large size classes
    const statusContainer = container.querySelector('.px-4.py-3.text-base');
    expect(statusContainer).toBeInTheDocument();
  });

  test('should show reconnection attempts in description', () => {
    useWebSocket.mockReturnValue({
      isConnected: false,
      connectionStatus: 'disconnected',
      reconnectAttempts: 5,
      lastConnectionTime: null,
      lastDataTime: null,
      connectionQuality: 'poor'
    });

    render(<WebSocketStatus showDetails={true} />, { wrapper });

    expect(screen.getByText('Reconnecting... (attempt 5)')).toBeInTheDocument();
  });

  test('should format time display correctly', () => {
    const oneMinuteAgo = new Date(Date.now() - 60000);
    const thirtySecondsAgo = new Date(Date.now() - 30000);

    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: oneMinuteAgo,
      lastDataTime: thirtySecondsAgo,
      connectionQuality: 'good'
    });

    render(<WebSocketStatus showDetails={true} />, { wrapper });

    expect(screen.getByText(/1m ago/)).toBeInTheDocument();
    expect(screen.getByText(/30s ago/)).toBeInTheDocument();
  });

  test('should apply custom className', () => {
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });

    const { container } = render(<WebSocketStatus className="custom-class" />, { wrapper });

    const statusContainer = container.querySelector('.custom-class');
    expect(statusContainer).toBeInTheDocument();
  });
});