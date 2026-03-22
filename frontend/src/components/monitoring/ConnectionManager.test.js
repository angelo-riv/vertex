/**
 * Connection Manager Component Tests
 * 
 * Tests for connection management and fallback functionality.
 * Validates requirements 7.2, 7.4, and 7.7 implementation.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConnectionManager from './ConnectionManager';
import { AppProvider } from '../../context/AppContext';

// Mock the useWebSocket hook
const mockUseWebSocket = jest.fn(() => ({
  isConnected: false,
  connectionStatus: 'disconnected',
  reconnectAttempts: 0,
  lastConnectionTime: null,
  lastDataTime: null,
  connectionQuality: 'poor',
  connect: jest.fn(),
  disconnect: jest.fn()
}));

jest.mock('../../hooks/useWebSocket', () => ({
  __esModule: true,
  default: mockUseWebSocket
}));

// Mock the useConnectionStatus hook
const mockUseConnectionStatus = jest.fn(() => ({
  isConnected: false,
  quality: 'poor',
  lastDataTime: null,
  deviceId: null,
  connectionFailures: 0,
  shouldSuggestDemo: false,
  diagnosticInfo: null,
  retryConnection: jest.fn(),
  dismissDemoSuggestion: jest.fn()
}));

jest.mock('../../hooks/useConnectionStatus', () => ({
  __esModule: true,
  default: mockUseConnectionStatus
}));

// Mock fetch for internet connectivity checks
global.fetch = jest.fn();

const renderWithProvider = (component) => {
  return render(
    <AppProvider>
      {component}
    </AppProvider>
  );
};

describe('ConnectionManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockResolvedValue({ ok: true });
  });

  describe('Connection Status Display', () => {
    test('displays ESP32 connected status when device is connected', () => {
      mockUseConnectionStatus.mockReturnValue({
        isConnected: true,
        quality: 'excellent',
        lastDataTime: new Date(),
        deviceId: 'ESP32_TEST',
        connectionFailures: 0,
        shouldSuggestDemo: false,
        diagnosticInfo: null,
        retryConnection: jest.fn(),
        dismissDemoSuggestion: jest.fn()
      });

      renderWithProvider(<ConnectionManager />);
      
      expect(screen.getByText('ESP32 Connected')).toBeInTheDocument();
      expect(screen.getByText(/Live data/)).toBeInTheDocument();
    });

    test('displays device disconnected message with last update time', () => {
      mockUseConnectionStatus.mockReturnValue({
        isConnected: false,
        quality: 'disconnected',
        lastDataTime: new Date(Date.now() - 60000), // 1 minute ago
        deviceId: null,
        connectionFailures: 1,
        shouldSuggestDemo: false,
        diagnosticInfo: null,
        retryConnection: jest.fn(),
        dismissDemoSuggestion: jest.fn()
      });
      
      renderWithProvider(<ConnectionManager />);
      
      expect(screen.getByText('Device Disconnected')).toBeInTheDocument();
      expect(screen.getByText(/ago/)).toBeInTheDocument();
    });
  });

  describe('Demo Mode Suggestion', () => {
    test('suggests demo mode after multiple connection failures', async () => {
      mockUseConnectionStatus.mockReturnValue({
        isConnected: false,
        quality: 'disconnected',
        lastDataTime: null,
        deviceId: null,
        connectionFailures: 3,
        shouldSuggestDemo: true,
        diagnosticInfo: null,
        retryConnection: jest.fn(),
        dismissDemoSuggestion: jest.fn()
      });

      renderWithProvider(<ConnectionManager />);
      
      expect(screen.getByText(/Multiple Connection Failures/)).toBeInTheDocument();
      expect(screen.getByText('Enable Demo Mode')).toBeInTheDocument();
    });

    test('calls demo mode toggle handler when activated', async () => {
      const mockDemoToggle = jest.fn();
      
      mockUseConnectionStatus.mockReturnValue({
        isConnected: false,
        quality: 'disconnected',
        lastDataTime: null,
        deviceId: null,
        connectionFailures: 3,
        shouldSuggestDemo: true,
        diagnosticInfo: null,
        retryConnection: jest.fn(),
        dismissDemoSuggestion: jest.fn()
      });
      
      renderWithProvider(
        <ConnectionManager onDemoModeActivate={mockDemoToggle} />
      );
      
      const demoButton = screen.getByText('Enable Demo Mode');
      fireEvent.click(demoButton);
      
      expect(mockDemoToggle).toHaveBeenCalled();
    });
  });

  describe('Internet Connectivity', () => {
    test('displays internet connected status', async () => {
      fetch.mockResolvedValue({ ok: true });
      
      renderWithProvider(<ConnectionManager showInternetStatus={true} />);
      
      await waitFor(() => {
        expect(screen.getByText(/Internet: Connected/)).toBeInTheDocument();
      });
    });

    test('displays internet disconnected status', async () => {
      fetch.mockRejectedValue(new Error('Network error'));
      
      renderWithProvider(<ConnectionManager showInternetStatus={true} />);
      
      await waitFor(() => {
        expect(screen.getByText(/Internet: Disconnected/)).toBeInTheDocument();
      });
    });

    test('shows internet status separately from ESP32 status', async () => {
      fetch.mockResolvedValue({ ok: true });
      
      renderWithProvider(<ConnectionManager />);
      
      await waitFor(() => {
        // Should show both ESP32 and internet status independently
        expect(screen.getByText('Device Disconnected')).toBeInTheDocument();
        expect(screen.getByText(/Internet: Connected/)).toBeInTheDocument();
      });
    });
  });

  describe('Connection Retry', () => {
    test('provides retry connection button when disconnected', () => {
      renderWithProvider(<ConnectionManager />);
      
      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();
    });

    test('calls retry handler when retry button clicked', () => {
      const mockRetry = jest.fn();
      
      renderWithProvider(
        <ConnectionManager onRetryConnection={mockRetry} />
      );
      
      const retryButton = screen.getByText('Retry');
      fireEvent.click(retryButton);
      
      expect(mockRetry).toHaveBeenCalled();
    });
  });

  describe('Data Freshness', () => {
    test('shows live data indicator for recent updates', () => {
      const useWebSocket = require('../../hooks/useWebSocket').default;
      useWebSocket.mockReturnValue({
        isConnected: true,
        lastDataTime: new Date(),
        connectionQuality: 'excellent'
      });

      renderWithProvider(<ConnectionManager />);
      
      expect(screen.getByText(/Live/)).toBeInTheDocument();
    });

    test('shows stale data warning for old updates', () => {
      const useWebSocket = require('../../hooks/useWebSocket').default;
      useWebSocket.mockReturnValue({
        isConnected: true,
        lastDataTime: new Date(Date.now() - 300000), // 5 minutes ago
        connectionQuality: 'poor'
      });

      renderWithProvider(<ConnectionManager />);
      
      expect(screen.getByText(/ago/)).toBeInTheDocument();
    });
  });

  describe('Diagnostic Information', () => {
    test('displays diagnostic info when available', () => {
      // This would test the diagnostic information display
      // Implementation depends on how diagnostic data is provided
      renderWithProvider(<ConnectionManager />);
      
      // Test diagnostic display when present
    });
  });
});

describe('ConnectionManager Integration', () => {
  test('integrates with AppContext for state management', () => {
    renderWithProvider(<ConnectionManager />);
    
    // Verify integration with app state
    expect(screen.getByText('Device Disconnected')).toBeInTheDocument();
  });

  test('updates display when connection state changes', async () => {
    const { rerender } = renderWithProvider(<ConnectionManager />);
    
    // Initial disconnected state
    expect(screen.getByText('Device Disconnected')).toBeInTheDocument();
    
    // Simulate connection
    const useWebSocket = require('../../hooks/useWebSocket').default;
    useWebSocket.mockReturnValue({
      isConnected: true,
      connectionStatus: 'connected',
      lastDataTime: new Date(),
      connectionQuality: 'excellent'
    });
    
    rerender(
      <AppProvider>
        <ConnectionManager />
      </AppProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('ESP32 Connected')).toBeInTheDocument();
    });
  });
});