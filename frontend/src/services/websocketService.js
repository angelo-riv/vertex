/**
 * WebSocket Service — singleton that owns the connection lifecycle.
 * Only WebSocketProvider should call connect/setEventListeners/cleanup.
 *
 * React 18 Strict Mode double-invokes effects in dev, so we handle the
 * mount → unmount → remount cycle gracefully:
 *   - cleanup() nulls listeners and sets a "dead" flag but does NOT close
 *     the socket immediately (avoids the 1006 error on the first mount).
 *   - connect() on the second mount reuses the existing socket if it is
 *     already OPEN or CONNECTING.
 */

const WS_URL = 'ws://192.168.1.110:8000/ws/sensor-stream';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectTimeout = null;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 5000;
    this.isConnecting = false;
    this.isManuallyDisconnected = false;
    this._currentUrl = WS_URL;

    this.onConnectionChange = null;
    this.onSensorData = null;
    this.onDeviceStatus = null;
    this.onError = null;

    this.connectionStatus = 'disconnected';
    this.lastConnectionTime = null;
    this.lastDataTime = null;
  }

  connect(url = WS_URL) {
    this._currentUrl = url;
    this.isManuallyDisconnected = false;

    // Already open — nothing to do
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected, skipping');
      return;
    }

    // Already connecting — nothing to do (second Strict Mode mount hits this)
    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      console.log('[WS] Already connecting, reusing socket');
      // Re-attach handlers in case they were nulled by cleanup()
      this._attachHandlers(this.ws, url);
      return;
    }

    this.isConnecting = true;
    this._updateStatus('connecting');
    console.log(`[WS] Connecting to ${url}`);

    const ws = new WebSocket(url);
    this.ws = ws;
    this._attachHandlers(ws, url);
  }

  _attachHandlers(ws, url) {
    ws.onopen = () => {
      if (this.ws !== ws) return; // stale socket
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.lastConnectionTime = new Date();
      this._clearReconnect();
      this._updateStatus('connected');
      console.log('[WS] Connected successfully');
      this.sendMessage({ type: 'ping' });
    };

    ws.onmessage = (event) => {
      if (this.ws !== ws) return;
      try {
        this._handleMessage(JSON.parse(event.data));
      } catch (e) {
        console.error('[WS] Parse error:', e);
      }
    };

    ws.onclose = (event) => {
      if (this.ws !== ws) return;
      this.isConnecting = false;
      console.log(`[WS] Closed — code=${event.code} reason="${event.reason}" manual=${this.isManuallyDisconnected}`);
      if (!this.isManuallyDisconnected) {
        this._updateStatus('disconnected');
        this._scheduleReconnect(url);
      }
    };

    ws.onerror = () => {
      if (this.ws !== ws) return;
      this.isConnecting = false;
      console.error('[WS] Connection error');
      this._updateStatus('error');
      if (this.onError) this.onError('WebSocket connection error');
    };
  }

  /**
   * Hard disconnect — used only when the app truly unmounts (not Strict Mode cleanup).
   */
  disconnect() {
    console.log('[WS] Manual disconnect');
    this.isManuallyDisconnected = true;
    this._clearReconnect();
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    this._updateStatus('disconnected');
  }

  /**
   * Soft cleanup — called by WebSocketProvider's useEffect cleanup.
   * Nulls listeners so stale callbacks don't fire, but keeps the socket
   * alive so the Strict Mode remount can reuse it.
   */
  cleanup() {
    console.log('[WS] Soft cleanup (listeners nulled, socket kept alive)');
    this.onConnectionChange = null;
    this.onSensorData = null;
    this.onDeviceStatus = null;
    this.onError = null;
  }

  _scheduleReconnect(url) {
    if (this.isManuallyDisconnected || this.reconnectTimeout) return;
    this.reconnectAttempts++;
    console.log(`[WS] Reconnect attempt ${this.reconnectAttempts} in ${this.reconnectDelay}ms`);
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      if (!this.isManuallyDisconnected) this.connect(url);
    }, this.reconnectDelay);
  }

  _clearReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  _handleMessage(data) {
    this.lastDataTime = new Date();
    switch (data.type) {
      case 'connected':
        console.log('[WS] Server confirmed connection');
        break;
      case 'sensor_data':
        console.log('[WS] Sensor data:', JSON.stringify(data.data).slice(0, 120));
        if (this.onSensorData) this.onSensorData(data.data);
        break;
      case 'device_status':
        console.log('[WS] Device status:', data.device_id, data.status);
        if (this.onDeviceStatus) this.onDeviceStatus(data.device_id, data.status);
        break;
      case 'pong':
      case 'keepalive':
        break;
      case 'status_response':
        if (this.onDeviceStatus) this.onDeviceStatus('system', { connected_devices: data.devices });
        break;
      default:
        console.log('[WS] Unknown message type:', data.type);
    }
  }

  _updateStatus(status) {
    if (this.connectionStatus === status) return;
    const prev = this.connectionStatus;
    this.connectionStatus = status;
    console.log(`[WS] Status: ${prev} → ${status}`);
    if (this.onConnectionChange) {
      this.onConnectionChange(status, {
        previousStatus: prev,
        reconnectAttempts: this.reconnectAttempts,
        lastConnectionTime: this.lastConnectionTime,
        lastDataTime: this.lastDataTime,
      });
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (e) {
        console.error('[WS] Send error:', e);
        return false;
      }
    }
    return false;
  }

  requestDeviceStatus() {
    return this.sendMessage({ type: 'request_device_status' });
  }

  getConnectionInfo() {
    return {
      status: this.connectionStatus,
      isConnected: this.connectionStatus === 'connected',
      reconnectAttempts: this.reconnectAttempts,
      lastConnectionTime: this.lastConnectionTime,
      lastDataTime: this.lastDataTime,
      readyState: this.ws ? this.ws.readyState : 3,
    };
  }

  setEventListeners(listeners) {
    this.onConnectionChange = listeners.onConnectionChange || null;
    this.onSensorData = listeners.onSensorData || null;
    this.onDeviceStatus = listeners.onDeviceStatus || null;
    this.onError = listeners.onError || null;
  }
}

export const websocketService = new WebSocketService();
export default websocketService;
