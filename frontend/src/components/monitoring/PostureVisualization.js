import React, { memo } from 'react';

const PostureVisualization = ({ 
  tiltAngle = 0, // Pitch angle in degrees (-180 to +180)
  size = 120,
  clinicalThresholds = { normal: 5, pusher: 10, severe: 20 }, // Clinical threshold markers
  calibrationBaseline = 0, // Calibrated baseline reference angle
  pusherDetected = false, // Pusher syndrome detection status
  connectionStatus = 'disconnected' // ESP32 connection status
}) => {
  // Clinical color coding based on pitch angle and pusher detection
  const getPostureColor = () => {
    const absAngle = Math.abs(tiltAngle - calibrationBaseline);
    
    // Clinical color coding with pusher syndrome consideration
    if (pusherDetected && absAngle >= clinicalThresholds.severe) {
      return '#dc2626'; // Red - Severe lean with pusher syndrome
    }
    if (pusherDetected && absAngle >= clinicalThresholds.pusher) {
      return '#f59e0b'; // Orange - Pusher syndrome detected
    }
    if (absAngle >= clinicalThresholds.severe) {
      return '#dc2626'; // Red - Severe lean (>15°)
    }
    if (absAngle >= clinicalThresholds.normal) {
      return '#f59e0b'; // Orange - Moderate lean (5-15°)
    }
    return '#22c55e'; // Green - Normal upright position (±5°)
  };

  // Calculate proportional rotation angle based on actual pitch
  const getRotationAngle = () => {
    // Use actual pitch angle relative to calibrated baseline
    const adjustedAngle = tiltAngle - calibrationBaseline;
    
    // Clamp rotation to ±30° for visual clarity while maintaining proportionality
    return Math.max(-30, Math.min(30, adjustedAngle));
  };

  // Determine lean direction based on pitch angle
  const getLeanDirection = () => {
    const adjustedAngle = tiltAngle - calibrationBaseline;
    const absAngle = Math.abs(adjustedAngle);
    
    if (absAngle <= clinicalThresholds.normal) {
      return 'upright';
    }
    return adjustedAngle > 0 ? 'right_lean' : 'left_lean';
  };

  const rotationAngle = getRotationAngle();
  const postureColor = getPostureColor();

  // Clinical threshold markers component
  const ClinicalThresholdMarkers = () => (
    <g opacity="0.3">
      {/* Normal threshold marker (±5°) */}
      <circle
        cx={size/2}
        cy={size/2}
        r={size * 0.42}
        fill="none"
        stroke="#22c55e"
        strokeWidth="1"
        strokeDasharray="3,2"
      />
      
      {/* Pusher threshold marker (±10°) */}
      <circle
        cx={size/2}
        cy={size/2}
        r={size * 0.38}
        fill="none"
        stroke="#f59e0b"
        strokeWidth="1"
        strokeDasharray="3,2"
      />
      
      {/* Severe threshold marker (±20°) */}
      <circle
        cx={size/2}
        cy={size/2}
        r={size * 0.32}
        fill="none"
        stroke="#dc2626"
        strokeWidth="1"
        strokeDasharray="3,2"
      />
      
      {/* Calibration baseline reference line */}
      {calibrationBaseline !== 0 && (
        <line
          x1={size/2}
          y1={size * 0.1}
          x2={size/2}
          y2={size * 0.9}
          stroke="#3b82f6"
          strokeWidth="2"
          strokeDasharray="4,4"
          opacity="0.6"
          transform={`rotate(${calibrationBaseline} ${size/2} ${size/2})`}
        />
      )}
    </g>
  );

  // Human figure SVG path with enhanced clinical styling
  const HumanFigure = () => (
    <g
      transform={`rotate(${rotationAngle} ${size/2} ${size/2})`}
      style={{
        transition: 'transform 50ms ease-out', // Reduced from 100ms to 50ms for faster updates
        transformOrigin: `${size/2}px ${size/2}px`
      }}
    >
      {/* Head */}
      <circle
        cx={size/2}
        cy={size * 0.15}
        r={size * 0.08}
        fill="none"
        stroke={postureColor}
        strokeWidth="3"
        strokeLinecap="round"
      />
      
      {/* Torso - thicker for better clinical visibility */}
      <line
        x1={size/2}
        y1={size * 0.23}
        x2={size/2}
        y2={size * 0.65}
        stroke={postureColor}
        strokeWidth="5"
        strokeLinecap="round"
      />
      
      {/* Left Arm */}
      <line
        x1={size/2}
        y1={size * 0.35}
        x2={size * 0.25}
        y2={size * 0.55}
        stroke={postureColor}
        strokeWidth="3"
        strokeLinecap="round"
      />
      
      {/* Right Arm */}
      <line
        x1={size/2}
        y1={size * 0.35}
        x2={size * 0.75}
        y2={size * 0.55}
        stroke={postureColor}
        strokeWidth="3"
        strokeLinecap="round"
      />
      
      {/* Left Leg */}
      <line
        x1={size/2}
        y1={size * 0.65}
        x2={size * 0.35}
        y2={size * 0.9}
        stroke={postureColor}
        strokeWidth="3"
        strokeLinecap="round"
      />
      
      {/* Right Leg */}
      <line
        x1={size/2}
        y1={size * 0.65}
        x2={size * 0.65}
        y2={size * 0.9}
        stroke={postureColor}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </g>
  );

  // Background gradient based on clinical status
  const getBackgroundGradient = () => {
    const absAngle = Math.abs(tiltAngle - calibrationBaseline);
    
    if (pusherDetected) {
      return (
        <defs>
          <radialGradient id="pusherGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fef2f2" />
            <stop offset="100%" stopColor="#fee2e2" />
          </radialGradient>
        </defs>
      );
    }
    
    if (absAngle >= clinicalThresholds.severe) {
      return (
        <defs>
          <radialGradient id="severeGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fef2f2" />
            <stop offset="100%" stopColor="#fee2e2" />
          </radialGradient>
        </defs>
      );
    }
    
    if (absAngle >= clinicalThresholds.normal) {
      return (
        <defs>
          <radialGradient id="moderateGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#fef3c7" />
            <stop offset="100%" stopColor="#fde68a" />
          </radialGradient>
        </defs>
      );
    }
    
    return (
      <defs>
        <radialGradient id="normalGradient" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f0fdf4" />
          <stop offset="100%" stopColor="#dcfce7" />
        </radialGradient>
      </defs>
    );
  };

  const getBackgroundFill = () => {
    const absAngle = Math.abs(tiltAngle - calibrationBaseline);
    
    if (pusherDetected) return 'url(#pusherGradient)';
    if (absAngle >= clinicalThresholds.severe) return 'url(#severeGradient)';
    if (absAngle >= clinicalThresholds.normal) return 'url(#moderateGradient)';
    return 'url(#normalGradient)';
  };

  // Clinical status text with enhanced information
  const getStatusText = () => {
    const absAngle = Math.abs(tiltAngle - calibrationBaseline);
    
    if (pusherDetected) {
      return 'Pusher Syndrome Detected';
    }
    
    if (absAngle <= clinicalThresholds.normal) {
      return 'Normal Upright Position';
    }
    
    const direction = (tiltAngle - calibrationBaseline) > 0 ? 'Right' : 'Left';
    
    if (absAngle >= clinicalThresholds.severe) {
      return `Severe ${direction} Lean`;
    }
    
    if (absAngle >= clinicalThresholds.pusher) {
      return `Moderate ${direction} Lean`;
    }
    
    return `Mild ${direction} Lean`;
  };

  const getStatusColor = () => {
    if (pusherDetected) return '#dc2626';
    return postureColor;
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 'var(--spacing-3)'
    }}>
      {/* SVG Visualization */}
      <div style={{
        position: 'relative',
        width: `${size}px`,
        height: `${size}px`
      }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{
            overflow: 'visible'
          }}
        >
          {getBackgroundGradient()}
          
          {/* Clinical Threshold Markers */}
          <ClinicalThresholdMarkers />
          
          {/* Background Circle */}
          <circle
            cx={size/2}
            cy={size/2}
            r={size/2 - 2}
            fill={getBackgroundFill()}
            stroke="var(--gray-200)"
            strokeWidth="2"
          />
          
          {/* Center Reference Line (vertical) */}
          <line
            x1={size/2}
            y1={size * 0.1}
            x2={size/2}
            y2={size * 0.9}
            stroke="var(--gray-300)"
            strokeWidth="1"
            strokeDasharray="2,2"
            opacity="0.5"
          />
          
          {/* Human Figure */}
          <HumanFigure />
          
          {/* Tilt Angle Arc (enhanced for clinical use) */}
          {Math.abs(rotationAngle) > 2 && (
            <path
              d={`M ${size/2} ${size * 0.3} A ${size * 0.2} ${size * 0.2} 0 0 ${rotationAngle > 0 ? 1 : 0} ${size/2 + Math.sin(rotationAngle * Math.PI / 180) * size * 0.2} ${size * 0.3 - Math.cos(rotationAngle * Math.PI / 180) * size * 0.2 + size * 0.2}`}
              fill="none"
              stroke={postureColor}
              strokeWidth="2"
              opacity="0.8"
            />
          )}
        </svg>
        
        {/* Enhanced Tilt Angle Display with Clinical Information */}
        {Math.abs(tiltAngle - calibrationBaseline) > 0.5 && (
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            padding: 'var(--spacing-1) var(--spacing-2)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: '600',
            color: postureColor,
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            border: `1px solid ${postureColor}`,
            minWidth: '45px',
            textAlign: 'center'
          }}>
            <div>{Math.abs(tiltAngle - calibrationBaseline).toFixed(1)}°</div>
            {pusherDetected && (
              <div style={{
                fontSize: 'var(--font-size-2xs)',
                color: '#dc2626',
                marginTop: '2px'
              }}>
                PUSHER
              </div>
            )}
          </div>
        )}
        
        {/* ESP32 Connection Status Indicator */}
        <div style={{
          position: 'absolute',
          top: '8px',
          left: '8px',
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: connectionStatus === 'connected' ? '#22c55e' : '#dc2626',
          boxShadow: '0 0 4px rgba(0, 0, 0, 0.2)'
        }} />
        
        {/* Calibration Status Indicator */}
        {calibrationBaseline !== 0 && (
          <div style={{
            position: 'absolute',
            bottom: '8px',
            right: '8px',
            backgroundColor: 'rgba(59, 130, 246, 0.9)',
            color: 'white',
            padding: '2px 6px',
            borderRadius: 'var(--border-radius-xs)',
            fontSize: 'var(--font-size-2xs)',
            fontWeight: '500'
          }}>
            CAL
          </div>
        )}
      </div>

      {/* Enhanced Status Text with Clinical Information */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: getStatusColor(),
          marginBottom: 'var(--spacing-1)'
        }}>
          {getStatusText()}
        </div>
        
        {/* Clinical Details */}
        <div style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--gray-600)',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px'
        }}>
          <div>
            Angle: {(tiltAngle - calibrationBaseline).toFixed(1)}° 
            {Math.abs(tiltAngle - calibrationBaseline) > clinicalThresholds.normal && 
              ` ${(tiltAngle - calibrationBaseline) > 0 ? 'Right' : 'Left'}`
            }
          </div>
          
          {calibrationBaseline !== 0 && (
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--gray-500)' }}>
              Baseline: {calibrationBaseline.toFixed(1)}°
            </div>
          )}
          
          {pusherDetected && (
            <div style={{
              fontSize: 'var(--font-size-xs)',
              color: '#dc2626',
              fontWeight: '600',
              marginTop: '4px'
            }}>
              ⚠️ Clinical Intervention Recommended
            </div>
          )}
        </div>
      </div>
      
      {/* Clinical Threshold Legend */}
      <div style={{
        fontSize: 'var(--font-size-2xs)',
        color: 'var(--gray-500)',
        textAlign: 'center',
        marginTop: 'var(--spacing-2)',
        display: 'flex',
        justifyContent: 'center',
        gap: 'var(--spacing-3)'
      }}>
        <span style={{ color: '#22c55e' }}>●</span>
        <span>±{clinicalThresholds.normal}°</span>
        <span style={{ color: '#f59e0b' }}>●</span>
        <span>±{clinicalThresholds.pusher}°</span>
        <span style={{ color: '#dc2626' }}>●</span>
        <span>±{clinicalThresholds.severe}°</span>
      </div>
    </div>
  );
};

export default memo(PostureVisualization);