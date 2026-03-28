/**
 * Global flag — when active, WebSocketProvider skips posture updates
 * so demo keyboard controls (W/A/D) aren't overwritten by real sensor data.
 */
let _active = false;
let _timer = null;

const demoOverride = {
  activate(ms = 5000) {
    _active = true;
    if (_timer) clearTimeout(_timer);
    _timer = setTimeout(() => { _active = false; }, ms);
  },
  isActive() { return _active; },
  clear() { _active = false; if (_timer) clearTimeout(_timer); }
};

export default demoOverride;
