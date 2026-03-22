/**
 * WebSocket Service for Real-time ESP32 Sensor Data
 * 
 * Manages WebSocket connection to FastAPI backend for receiving real-time sensor data.
 * Implements automatic reconnection, connection status tracking, and message handling.
 * 
 * Requirements implemented:
 * - 4.1: Establish WebSocket connection to FastAPI backend on component mount
 * - 4.5: Implement automatic reconnection every 5 seconds on connection failure
 * - 7.1: Add connection status indicators (green for connected, red for disconnected)
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectInterval = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = Infinity; // Keep trying indefinitely
    this.reconnectDelay = 5000; // 5 seconds
    this.isConnecting = false;
    this.isManuallyDisconnected = false;
    
    // Event listeners
    this.onConnectionChange = null;
    this.onSensorData = null;
    this.onDeviceStatus = null;
    this.onError = null;
    
    // Connection status
    this.connectionStatus = 'disconnected'; // 'connecting', 'connected', 'disconnected', 'error'
    this.lastConnectionTime = null;
    this.lastDataTime = null;
  }

  /**
   * Connect to WebSocket server with optimized connection handling
   * @param {string} url - WebSocket URL (default: ws://localhost:8000/ws/sensor-stream)
   */
  connect(url = 'ws://localhost:8000/ws/sensor-stream') {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;
    this.isManuallyDisconnected = false;
    this.updateConnectionStatus('connecting');

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = (event) => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.lastConnectionTime = new Date();
        this.updateConnectionStatus('connected');
        
        // Clear reconnect interval
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval);
          this.reconnectInterval = null;
        }

        // Send minimal ping
        this.sendMessage({ type: 'ping' });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('WebSocket parse error:', error);
        }
      };

      this.ws.onclose = (event) => {
        this.isConnecting = false;
        
        if (!this.isManuallyDisconnected) {
          this.updateConnectionStatus('disconnected');
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        this.isConnecting = false;
        this.updateConnectionStatus('error');
        
        if (this.onError) {
          this.onError('WebSocket connection error');
        }
      };

    } catch (error) {
      this.isConnecting = false;
      this.updateConnectionStatus('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    console.log('Manually disconnecting WebSocket');
    this.isManuallyDisconnected = true;
    
    // Clear reconnect interval
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
      this.reconnectInterval = null;
    }

    // Close WebSocket connection
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }

    this.updateConnectionStatus('disconnected');
  }

  /**
   * Schedule automatic reconnection
   */
  scheduleReconnect() {
    if (this.isManuallyDisconnected || this.reconnectInterval) {
      return;
    }

    this.reconnectAttempts++;
    console.log(`Scheduling WebSocket reconnection attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);

    this.reconnectInterval = setTimeout(() => {
      this.reconnectInterval = null;
      
      if (!this.isManuallyDisconnected) {
        console.log(`WebSocket reconnection attempt ${this.reconnectAttempts}`);
        this.connect();
      }
    }, this.reconnectDelay);
  }

  /**
   * Send message to WebSocket server
   * @param {object} message - Message to send
   */
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket not connected, cannot send message:', message);
      return false;
    }
  }

  /**
   * Handle incoming WebSocket messages with optimized processing for real-time updates
   * @param {object} data - Parsed message data
   */
  handleMessage(data) {
    this.lastDataTime = new Date();

    // Optimized message handling - process sensor data immediately without requestAnimationFrame
    // to meet sub-50ms rendering requirement
    switch (data.type) {
      case 'connected':
        console.log('WebSocket connection established');
        break;

      case 'sensor_data':
        // Critical path: Process sensor data immediately for sub-50ms updates
        if (this.onSensorData) {
          this.onSensorData(data.data);
        }
        break;

      case 'device_status':
        if (this.onDeviceStatus) {
          this.onDeviceStatus(data.device_id, data.status);
        }
        break;

      case 'pong':
        // Minimal pong handling
        break;

      case 'keepalive':
        // Server keepalive - no action needed
        break;

      case 'status_response':
        if (this.onDeviceStatus) {
          this.onDeviceStatus('system', { connected_devices: data.devices });
        }
        break;

      default:
        // Minimal logging for unknown messages
        if (data.type !== 'keepalive') {
          console.log('Unknown WebSocket message:', data.type);
        }
    }
  }

  /**
   * Update connection status and notify listeners
   * @param {string} status - New connection status
   */
  updateConnectionStatus(status) {
    if (this.connectionStatus !== status) {
      const previousStatus = this.connectionStatus;
      this.connectionStatus = status;
      
      console.log(`WebSocket status changed: ${previousStatus} -> ${status}`);
      
      if (this.onConnectionChange) {
        this.onConnectionChange(status, {
          previousStatus,
          reconnectAttempts: this.reconnectAttempts,
          lastConnectionTime: this.lastConnectionTime,
          lastDataTime: this.lastDataTime
        });
      }
    }
  }

  /**
   * Request device status from server
   */
  requestDeviceStatus() {
    return this.sendMessage({ type: 'request_device_status' });
  }

  /**
   * Request connection statistics from server
   */
  requestConnectionStats() {
    return this.sendMessage({ type: 'request_connection_stats' });
  }

  /**
   * Get current connection status
   * @returns {object} Connection status information
   */
  getConnectionInfo() {
    return {
      status: this.connectionStatus,
      isConnected: this.connectionStatus === 'connected',
      reconnectAttempts: this.reconnectAttempts,
      lastConnectionTime: this.lastConnectionTime,
      lastDataTime: this.lastDataTime,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED
    };
  }

  /**
   * Set event listeners
   * @param {object} listeners - Event listener functions
   */
  setEventListeners(listeners) {
    this.onConnectionChange = listeners.onConnectionChange || null;
    this.onSensorData = listeners.onSensorData || null;
    this.onDeviceStatus = listeners.onDeviceStatus || null;
    this.onError = listeners.onError || null;
  }

  /**
   * Clean up resources
   */
  cleanup() {
    this.disconnect();
    this.onConnectionChange = null;
    this.onSensorData = null;
    this.onDeviceStatus = null;
    this.onError = null;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;