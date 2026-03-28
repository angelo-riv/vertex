/**
 * useDemoControls — global keyboard demo override.
 * W = upright, A = lean left, D = lean right
 *
 * Once a key is pressed, continuously streams fake "live" sensor data
 * with smooth sine-wave variation until a different key is pressed.
 * Keeps demoOverride active indefinitely so real WS data never overwrites it.
 */

import { useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import demoOverride from '../services/demoOverride';

export const useDemoControls = () => {
  const { actions } = useApp();
  const actionsRef = useRef(actions);
  const modeRef = useRef(null);
  const intervalRef = useRef(null);
  const tRef = useRef(0); // time counter for smooth sine drift

  useEffect(() => { actionsRef.current = actions; }, [actions]);

  useEffect(() => {
    const startStreaming = (mode) => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      modeRef.current = mode;
      tRef.current = 0;

      intervalRef.current = setInterval(() => {
        tRef.current += 0.15; // advance time
        const t = tRef.current;

        // Smooth sine drift — looks like real sensor noise
        const drift = Math.sin(t) * 1.8 + Math.sin(t * 2.3) * 0.6 + Math.sin(t * 0.7) * 0.4;

        let base, tiltDirection, alertLevel;

        if (mode === 'left') {
          base = -20 + drift;
          tiltDirection = 'left';
          alertLevel = Math.abs(base) >= 15 ? 'danger' : 'warning';
        } else if (mode === 'right') {
          base = 20 + drift;
          tiltDirection = 'right';
          alertLevel = Math.abs(base) >= 15 ? 'danger' : 'warning';
        } else {
          base = drift * 0.4; // tiny sway around 0
          tiltDirection = Math.abs(base) < 2 ? 'center' : base < 0 ? 'left' : 'right';
          alertLevel = 'normal';
        }

        const tiltAngle = parseFloat(base.toFixed(1));
        const fsrNoise = () => Math.round(Math.random() * 80);

        // Keep override alive — never let real WS data overwrite
        demoOverride.activate(999999);

        actionsRef.current.updateLivePosture({
          tiltAngle,
          tiltDirection,
          alertLevel,
          fsrLeft:  mode === 'left'  ? 600 + fsrNoise() : 80 + fsrNoise(),
          fsrRight: mode === 'right' ? 600 + fsrNoise() : 80 + fsrNoise(),
          balance:  mode === 'left'  ? -0.55 : mode === 'right' ? 0.55 : drift * 0.05,
          hapticActive: alertLevel !== 'normal',
        });

        actionsRef.current.setESP32Connection({ isConnected: true, deviceId: 'ESP32_cdffc9ec' });
        actionsRef.current.updateESP32Status({ lastDataTimestamp: new Date(), connectionQuality: 'excellent' });
        actionsRef.current.setAlertLevel(
          alertLevel === 'danger' ? 'unsafe' : alertLevel === 'warning' ? 'warning' : 'safe'
        );
      }, 150); // ~6Hz, same as real ESP32
    };

    const handleKey = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      let mode = null;
      if (!e || typeof e.key !== 'string') return; // guard against synthetic/autofill events
      switch (e.key.toLowerCase()) {
        case 'a': mode = 'left';   break;
        case 'd': mode = 'right';  break;
        case 'w': mode = 'center'; break;
        default: return;
      }

      if (modeRef.current === mode) return; // already streaming this mode
      console.log(`[DemoControls] ${e.key.toUpperCase()} → mode: ${mode}`);
      startStreaming(mode);
    };

    window.addEventListener('keydown', handleKey);
    return () => {
      window.removeEventListener('keydown', handleKey);
      if (intervalRef.current) clearInterval(intervalRef.current);
      demoOverride.clear();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
};

export default useDemoControls;
