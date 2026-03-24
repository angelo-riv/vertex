/**
 * WebSocketProvider — sole owner of the WebSocket connection.
 * Connects once on mount, stays alive, feeds AppContext with live data.
 */

import React, { useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import websocketService from '../../services/websocketService';

const WS_URL = 'ws://192.168.1.110:8000/ws/sensor-stream';

const WebSocketProvider = ({ children }) => {
  const { actions } = useApp();
  const actionsRef = useRef(actions);
  useEffect(() => { actionsRef.current = actions; }, [actions]);

  useEffect(() => {
    console.log('[WebSocketProvider] Mounting — registering listeners and connecting to', WS_URL);

    websocketService.setEventListeners({
      onConnectionChange: (status) => {
        console.log('[WebSocketProvider] Connection changed:', status);
        const isConnected = status === 'connected';
        actionsRef.current.setDeviceConnection({ isConnected, deviceId: isConnected ? 'websocket-client' : null });
        if (!isConnected) {
          actionsRef.current.setESP32Connection({ isConnected: false, deviceId: null });
        }
      },

      onSensorData: (data) => {
        // Backend shortened keys: d=device_id, ta=tilt_angle, td=tilt_direction,
        // fl=fsr_left, fr=fsr_right, al=alert_level, b=balance,
        // pd=pusher_detected, ss=severity_score, cl=confidence_level
        const deviceId   = data.d  ?? data.device_id;
        const tiltAngle  = data.ta ?? data.processed_data?.tilt_angle   ?? 0;
        const tiltDir    = data.td ?? data.processed_data?.tilt_direction ?? 'center';
        const fsrLeft    = data.fl ?? data.raw_data?.fsr_left  ?? 0;
        const fsrRight   = data.fr ?? data.raw_data?.fsr_right ?? 0;
        const alertLevel = data.al ?? data.processed_data?.alert_level  ?? 'normal';
        const balance    = data.b  ?? data.processed_data?.fsr_balance  ?? 0;
        const pusher     = data.pd ?? data.clinical_analysis?.pusher_detected ?? false;
        const severity   = data.ss ?? data.clinical_analysis?.severity_score  ?? 0;

        console.log(`[WebSocketProvider] Sensor data — device=${deviceId} tilt=${tiltAngle}° dir=${tiltDir} alert=${alertLevel}`);

        if (deviceId) {
          actionsRef.current.setESP32Connection({ isConnected: true, deviceId });
          actionsRef.current.updateESP32Status({ lastDataTimestamp: new Date(), connectionQuality: 'excellent' });
        }

        actionsRef.current.updateLivePosture({
          tiltAngle,
          tiltDirection: tiltDir,
          fsrLeft,
          fsrRight,
          balance,
          alertLevel,
          hapticActive: alertLevel !== 'normal' && alertLevel !== 'safe',
        });

        const mappedLevel =
          alertLevel === 'danger'  ? 'unsafe'  :
          alertLevel === 'warning' ? 'warning' : 'safe';
        actionsRef.current.setAlertLevel(mappedLevel);

        if (pusher !== undefined) actionsRef.current.setPusherDetected(pusher, severity);
        if (severity !== undefined) actionsRef.current.updateClinicalScore(severity);
      },

      onDeviceStatus: (deviceId, status) => {
        console.log('[WebSocketProvider] Device status:', deviceId, status);
        const isConnected = status.connection_status === 'connected' || status.connected_devices > 0;
        actionsRef.current.setESP32Connection({ isConnected, deviceId: isConnected ? deviceId : null });
      },

      onError: (err) => {
        console.error('[WebSocketProvider] WebSocket error:', err);
        actionsRef.current.setESP32Connection({ isConnected: false, deviceId: null });
      },
    });

    websocketService.connect(WS_URL);

    return () => {
      // Soft cleanup: null the listeners so stale callbacks don't fire.
      // We do NOT disconnect the socket here because React 18 Strict Mode
      // unmounts and remounts every effect in dev — a hard disconnect would
      // kill the socket before the second mount can reuse it.
      console.log('[WebSocketProvider] Effect cleanup — nulling listeners (socket kept alive)');
      websocketService.cleanup();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>;
};

export default WebSocketProvider;
