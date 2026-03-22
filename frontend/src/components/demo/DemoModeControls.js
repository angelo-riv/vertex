import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';

const DemoModeControls = () => {
  const { state, actions } = useApp();
  const { demo } = state;
  const [isLoading, setIsLoading] = useState(false);
  const [availableScenarios, setAvailableScenarios] = useState([]);
  const [error, setError] = useState(null);

  // Fetch available scenarios on component mount
  useEffect(() => {
    fetchAvailableScenarios();
  }, []);

  const fetchAvailableScenarios = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/demo/scenarios');
      if (response.ok) {
        const data = await response.json();
        setAvailableScenarios(data.scenarios || []);
      }
    } catch (error) {
      console.error('Failed to fetch demo scenarios:', error);
    }
  };

  const handleToggleDemoMode = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const enabled = !demo.isActive;
      const deviceId = 'ESP32_DEMO_PRESENTATION';
      
      const response = await fetch(
        `http://localhost:8000/api/demo/toggle?enabled=${enabled}&device_id=${deviceId}`,
        { method: 'POST' }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('Demo toggle result:', result);
        
        if (enabled) {
          actions.startDemoMode(deviceId, 'normal_posture');
          actions.addNotification('Demo mode activated - simulated data active', 'success');
        } else {
          actions.stopDemoMode();
          actions.addNotification('Demo mode deactivated - returning to live data', 'info');
        }
      } else {
        throw new Error('Failed to toggle demo mode');
      }
    } catch (error) {
      console.error('Demo mode toggle error:', error);
      setError('Failed to toggle demo mode. Please check backend connection.');
      actions.addError('Demo mode toggle failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleScenarioChange = async (scenarioName) => {
    if (!demo.isActive) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/demo/scenario/${scenarioName}`,
        { method: 'POST' }
      );

      if (response.ok) {
        actions.setDemoScenario(scenarioName);
        actions.addNotification(`Demo scenario changed to ${scenarioName}`, 'info');
      } else {
        throw new Error('Failed to change demo scenario');
      }
    } catch (error) {
      console.error('Scenario change error:', error);
      setError('Failed to change scenario');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid var(--gray-200)',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--spacing-4)',
      marginBottom: 'var(--spacing-4)',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 'var(--spacing-3)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="10,8 16,12 10,16 10,8"/>
          </svg>
          Demo Mode Controls
        </h3>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          {demo.isActive && (
            <span style={{
              fontSize: 'var(--font-size-sm)',
              color: '#ff4444',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <div style={{
                width: '6px',
                height: '6px',
                backgroundColor: '#ff4444',
                borderRadius: '50%',
                animation: 'blink 1s infinite'
              }} />
              LIVE DEMO
            </span>
          )}

          <button
            onClick={handleToggleDemoMode}
            disabled={isLoading}
            style={{
              backgroundColor: demo.isActive ? '#dc2626' : 'var(--primary-blue)',
              color: 'white',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--spacing-2) var(--spacing-4)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '600',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.7 : 1,
              transition: 'var(--transition-fast)',
              minWidth: '100px'
            }}
          >
            {isLoading ? 'Loading...' : demo.isActive ? 'Stop Demo' : 'Start Demo'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--spacing-3)',
          marginBottom: 'var(--spacing-3)',
          color: '#dc2626',
          fontSize: 'var(--font-size-sm)'
        }}>
          {error}
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 'var(--spacing-3)',
        marginBottom: 'var(--spacing-3)'
      }}>
        <div>
          <label style={{
            display: 'block',
            fontSize: 'var(--font-size-sm)',
            fontWeight: '500',
            color: 'var(--gray-700)',
            marginBottom: 'var(--spacing-1)'
          }}>
            Status
          </label>
          <div style={{
            padding: 'var(--spacing-2)',
            backgroundColor: demo.isActive ? '#fef2f2' : '#f0f9ff',
            border: `1px solid ${demo.isActive ? '#fecaca' : '#bae6fd'}`,
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
            color: demo.isActive ? '#dc2626' : '#0369a1',
            fontWeight: '500'
          }}>
            {demo.isActive ? 'Demo Mode Active' : 'Live Hardware Mode'}
          </div>
        </div>

        {demo.isActive && (
          <div>
            <label style={{
              display: 'block',
              fontSize: 'var(--font-size-sm)',
              fontWeight: '500',
              color: 'var(--gray-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Device ID
            </label>
            <div style={{
              padding: 'var(--spacing-2)',
              backgroundColor: 'var(--gray-50)',
              border: '1px solid var(--gray-200)',
              borderRadius: 'var(--radius-md)',
              fontSize: 'var(--font-size-sm)',
              color: 'var(--gray-600)',
              fontFamily: 'monospace'
            }}>
              {demo.deviceId || 'N/A'}
            </div>
          </div>
        )}
      </div>

      {demo.isActive && availableScenarios.length > 0 && (
        <div>
          <label style={{
            display: 'block',
            fontSize: 'var(--font-size-sm)',
            fontWeight: '500',
            color: 'var(--gray-700)',
            marginBottom: 'var(--spacing-2)'
          }}>
            Demo Scenario
          </label>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 'var(--spacing-2)'
          }}>
            {availableScenarios.map((scenario) => (
              <button
                key={scenario.name}
                onClick={() => handleScenarioChange(scenario.name)}
                disabled={isLoading}
                style={{
                  padding: 'var(--spacing-2)',
                  backgroundColor: demo.currentScenario === scenario.name ? 'var(--primary-blue)' : 'white',
                  color: demo.currentScenario === scenario.name ? 'white' : 'var(--gray-700)',
                  border: `1px solid ${demo.currentScenario === scenario.name ? 'var(--primary-blue)' : 'var(--gray-300)'}`,
                  borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--font-size-xs)',
                  fontWeight: '500',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading ? 0.7 : 1,
                  transition: 'var(--transition-fast)',
                  textAlign: 'center'
                }}
                title={scenario.description}
              >
                <div style={{ fontWeight: '600' }}>
                  {scenario.display_name}
                </div>
                <div style={{ 
                  fontSize: '10px', 
                  opacity: 0.8,
                  marginTop: '2px'
                }}>
                  {scenario.pitch_range}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{
        marginTop: 'var(--spacing-3)',
        padding: 'var(--spacing-3)',
        backgroundColor: '#f0f9ff',
        border: '1px solid #bae6fd',
        borderRadius: 'var(--radius-md)',
        fontSize: 'var(--font-size-sm)',
        color: '#0369a1'
      }}>
        <div style={{ fontWeight: '600', marginBottom: 'var(--spacing-1)' }}>
          📡 Internet Connectivity Status
        </div>
        <div>
          Full internet access maintained during demo mode. Supabase and external services remain accessible.
        </div>
      </div>

      <style jsx>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

export default DemoModeControls;