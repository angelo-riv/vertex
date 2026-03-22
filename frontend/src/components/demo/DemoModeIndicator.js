import React from 'react';
import { useApp } from '../../context/AppContext';

const DemoModeIndicator = () => {
  const { state } = useApp();
  const { demo } = state;

  if (!demo.isActive) {
    return null;
  }

  const getDuration = () => {
    if (!demo.startTime) return '0s';
    const now = new Date();
    const duration = Math.floor((now - demo.startTime) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };

  const getScenarioDisplayName = (scenario) => {
    const scenarioNames = {
      'normal_posture': 'Normal Posture',
      'mild_pusher_episode': 'Mild Pusher',
      'moderate_pusher_episode': 'Moderate Pusher',
      'severe_pusher_episode': 'Severe Pusher',
      'correction_attempt': 'Correction',
      'recovery_phase': 'Recovery'
    };
    return scenarioNames[scenario] || scenario;
  };

  return (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      backgroundColor: '#ff4444',
      color: 'white',
      padding: '8px 16px',
      borderRadius: '8px',
      fontSize: '14px',
      fontWeight: 'bold',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(255, 68, 68, 0.3)',
      border: '2px solid #ff6666',
      animation: 'pulse 2s infinite',
      minWidth: '120px',
      textAlign: 'center'
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        gap: '8px'
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          backgroundColor: 'white',
          borderRadius: '50%',
          animation: 'blink 1s infinite'
        }} />
        <span>DEMO MODE</span>
      </div>
      
      <div style={{
        fontSize: '11px',
        marginTop: '4px',
        opacity: 0.9,
        fontWeight: 'normal'
      }}>
        {getScenarioDisplayName(demo.currentScenario)}
      </div>
      
      <div style={{
        fontSize: '10px',
        marginTop: '2px',
        opacity: 0.8,
        fontWeight: 'normal'
      }}>
        {getDuration()}
      </div>

      <style jsx>{`
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

export default DemoModeIndicator;