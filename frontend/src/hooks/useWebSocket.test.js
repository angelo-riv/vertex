/**
 * Tests for useWebSocket Hook
 * 
 * Tests WebSocket connection management, automatic reconnection,
 * and integration with AppContext state management.
 */

import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import { AppProvider } from '../context/AppContext';
import websocketService from '../services/websocketService';

// Mock the WebSocket service
jest.mock('../services/websocketService', () => ({
  connect: jest.fn(),
  disconnect: jest.fn(),
  sendMessage: jest.fn(),
  requestDeviceStatus: jest.fn(),
  getConnectionInfo: jest.fn(() => ({
    status: 'disconnected',
    isConnected: false,
    reconnectAttempts: 0,
    lastConnectionTime: null,
    lastDataTime: null,
    readyState: WebSocket.CLOSED
  })),
  setEventListeners: jest.fn(),
  cleanup: jest.fn()
}));

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  close: jest.fn(),
  send: jest.fn(),
  readyState: WebSocket.CLOSED
}));

// WebSocket constants
global.WebSocket.CONNECTING = 0;
global.WebSocket.OPEN = 1;
global.WebSocket.CLOSING = 2;
global.WebSocket.CLOSED = 3;

const wrapper = ({ children }) => <AppProvider>{children}</AppProvider>;

describe('useWebSocket Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should initialize with default connection state', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionStatus).toBe('disconnected');
    expect(result.current.reconnectAttempts).toBe(0);
    expect(result.current.isConnecting).toBe(false);
    expect(result.current.hasError).toBe(false);
    expect(result.current.connectionQuality).toBe('poor');
  });

  test('should auto-connect when autoConnect is true', () => {
    renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

    expect(websocketService.connect).toHaveBeenCalledWith('ws://localhost:8000/ws/sensor-stream');
    expect(websocketService.setEventListeners).toHaveBeenCalled();
  });

  test('should not auto-connect when autoConnect is false', () => {
    renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(websocketService.connect).not.toHaveBeenCalled();
    expect(websocketService.setEventListeners).toHaveBeenCalled();
  });

  test('should use custom URL when provided', () => {
    const customUrl = 'ws://custom-server:9000/ws/test';
    renderHook(() => useWebSocket({ autoConnect: true, url: customUrl }), { wrapper });

    expect(websocketService.connect).toHaveBeenCalledWith(customUrl);
  });

  test('should provide connection methods', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(typeof result.current.connect).toBe('function');
    expect(typeof result.current.disconnect).toBe('function');
    expect(typeof result.current.sendMessage).toBe('function');
    expect(typeof result.current.requestDeviceStatus).toBe('function');
    expect(typeof result.current.getConnectionInfo).toBe('function');
  });

  test('should call connect method when connect is invoked', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    act(() => {
      result.current.connect();
    });

    expect(websocketService.connect).toHaveBeenCalledWith('ws://localhost:8000/ws/sensor-stream');
  });

  test('should call disconnect method when disconnect is invoked', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    act(() => {
      result.current.disconnect();
    });

    expect(websocketService.disconnect).toHaveBeenCalled();
  });

  test('should call sendMessage method when sendMessage is invoked', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });
    const testMessage = { type: 'test', data: 'hello' };

    act(() => {
      result.current.sendMessage(testMessage);
    });

    expect(websocketService.sendMessage).toHaveBeenCalledWith(testMessage);
  });

  test('should call requestDeviceStatus method when requestDeviceStatus is invoked', () => {
    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    act(() => {
      result.current.requestDeviceStatus();
    });

    expect(websocketService.requestDeviceStatus).toHaveBeenCalled();
  });

  test('should update connection quality based on connection status', () => {
    // Mock connected state with recent data
    websocketService.getConnectionInfo.mockReturnValue({
      status: 'connected',
      isConnected: true,
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(Date.now() - 1000), // 1 second ago
      readyState: WebSocket.OPEN
    });

    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionQuality).toBe('excellent');
  });

  test('should show good connection quality for older data', () => {
    // Mock connected state with older data
    websocketService.getConnectionInfo.mockReturnValue({
      status: 'connected',
      isConnected: true,
      reconnectAttempts: 0,
      lastConnectionTime: new Date(),
      lastDataTime: new Date(Date.now() - 10000), // 10 seconds ago
      readyState: WebSocket.OPEN
    });

    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.isConnected).toBe(true);
    expect(result.current.connectionQuality).toBe('good');
  });

  test('should show poor connection quality when disconnected', () => {
    websocketService.getConnectionInfo.mockReturnValue({
      status: 'disconnected',
      isConnected: false,
      reconnectAttempts: 3,
      lastConnectionTime: null,
      lastDataTime: null,
      readyState: WebSocket.CLOSED
    });

    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.isConnected).toBe(false);
    expect(result.current.connectionQuality).toBe('poor');
  });

  test('should detect connecting state', () => {
    websocketService.getConnectionInfo.mockReturnValue({
      status: 'connecting',
      isConnected: false,
      reconnectAttempts: 1,
      lastConnectionTime: null,
      lastDataTime: null,
      readyState: WebSocket.CONNECTING
    });

    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.isConnecting).toBe(true);
    expect(result.current.hasError).toBe(false);
  });

  test('should detect error state', () => {
    websocketService.getConnectionInfo.mockReturnValue({
      status: 'error',
      isConnected: false,
      reconnectAttempts: 2,
      lastConnectionTime: null,
      lastDataTime: null,
      readyState: WebSocket.CLOSED
    });

    const { result } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    expect(result.current.hasError).toBe(true);
    expect(result.current.isConnecting).toBe(false);
  });

  test('should cleanup on unmount when autoConnect is true', () => {
    const { unmount } = renderHook(() => useWebSocket({ autoConnect: true }), { wrapper });

    unmount();

    expect(websocketService.disconnect).toHaveBeenCalled();
    expect(websocketService.setEventListeners).toHaveBeenCalledWith({
      onConnectionChange: null,
      onSensorData: null,
      onDeviceStatus: null,
      onError: null
    });
  });

  test('should not cleanup on unmount when autoConnect is false', () => {
    const { unmount } = renderHook(() => useWebSocket({ autoConnect: false }), { wrapper });

    unmount();

    expect(websocketService.disconnect).not.toHaveBeenCalled();
    expect(websocketService.setEventListeners).toHaveBeenCalledWith({
      onConnectionChange: null,
      onSensorData: null,
      onDeviceStatus: null,
      onError: null
    });
  });
});