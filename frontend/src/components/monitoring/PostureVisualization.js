import React from 'react';

const PostureVisualization = ({ 
  postureState = 'upright', // 'upright', 'left_lean', 'right_lean'
  tiltAngle = 0,
  size = 120 
}) => {
  // Define colors based on posture state
  const getPostureColor = () => {
    switch (postureState) {
      case 'upright':
        return 'var(--primary-blue)'; // Correct posture - blue
      case 'left_lean':
      case 'right_lean':
        return tiltAngle > 15 ? '#dc2626' : '#f59e0b'; // Red for unsafe, amber for warning
      default:
        return 'var(--gray-400)';
    }
  };

  // Calculate rotation angle for the human figure
  const getRotationAngle = () => {
    switch (postureState) {
      case 'left_lean':
        return -Math.min(tiltAngle, 30); // Lean left (negative rotation)
      case 'right_lean':
        return Math.min(tiltAngle, 30); // Lean right (positive rotation)
      case 'upright':
      default:
        return 0; // Straight up
    }
  };

  const rotationAngle = getRotationAngle();
  const postureColor = getPostureColor();

  // Human figure SVG path (simplified line-art silhouette)
  const HumanFigure = () => (
    <g
      transform={`rotate(${rotationAngle} ${size/2} ${size/2})`}
      style={{
        transition: 'transform 300ms ease-in-out',
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
      
      {/* Torso */}
      <line
        x1={size/2}
        y1={size * 0.23}
        x2={size/2}
        y2={size * 0.65}
        stroke={postureColor}
        strokeWidth="4"
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

  // Background circle with gradient based on posture state
  const getBackgroundGradient = () => {
    switch (postureState) {
      case 'upright':
        return (
          <defs>
            <radialGradient id="uprightGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="var(--primary-blue-100)" />
              <stop offset="100%" stopColor="var(--primary-blue-50)" />
            </radialGradient>
          </defs>
        );
      case 'left_lean':
      case 'right_lean':
        const isUnsafe = tiltAngle > 15;
        return (
          <defs>
            <radialGradient id="leanGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={isUnsafe ? '#fef2f2' : '#fef3c7'} />
              <stop offset="100%" stopColor={isUnsafe ? '#fee2e2' : '#fde68a'} />
            </radialGradient>
          </defs>
        );
      default:
        return (
          <defs>
            <radialGradient id="defaultGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="var(--gray-100)" />
              <stop offset="100%" stopColor="var(--gray-50)" />
            </radialGradient>
          </defs>
        );
    }
  };

  const getBackgroundFill = () => {
    switch (postureState) {
      case 'upright':
        return 'url(#uprightGradient)';
      case 'left_lean':
      case 'right_lean':
        return 'url(#leanGradient)';
      default:
        return 'url(#defaultGradient)';
    }
  };

  // Status text
  const getStatusText = () => {
    switch (postureState) {
      case 'upright':
        return 'Upright Position';
      case 'left_lean':
        return 'Leaning Left';
      case 'right_lean':
        return 'Leaning Right';
      default:
        return 'Unknown Position';
    }
  };

  const getStatusColor = () => {
    switch (postureState) {
      case 'upright':
        return 'var(--primary-blue-700)';
      case 'left_lean':
      case 'right_lean':
        return tiltAngle > 15 ? '#dc2626' : '#d97706';
      default:
        return 'var(--gray-600)';
    }
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
          
          {/* Tilt Angle Arc (if leaning) */}
          {postureState !== 'upright' && Math.abs(rotationAngle) > 2 && (
            <path
              d={`M ${size/2} ${size * 0.3} A ${size * 0.2} ${size * 0.2} 0 0 ${rotationAngle > 0 ? 1 : 0} ${size/2 + Math.sin(rotationAngle * Math.PI / 180) * size * 0.2} ${size * 0.3 - Math.cos(rotationAngle * Math.PI / 180) * size * 0.2 + size * 0.2}`}
              fill="none"
              stroke={postureColor}
              strokeWidth="2"
              opacity="0.6"
            />
          )}
        </svg>
        
        {/* Tilt Angle Display */}
        {tiltAngle > 0 && (
          <div style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            padding: 'var(--spacing-1) var(--spacing-2)',
            borderRadius: 'var(--border-radius-sm)',
            fontSize: 'var(--font-size-xs)',
            fontWeight: '600',
            color: postureColor,
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            {tiltAngle.toFixed(1)}°
          </div>
        )}
      </div>

      {/* Status Text */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: getStatusColor(),
          marginBottom: 'var(--spacing-1)'
        }}>
          {getStatusText()}
        </div>
        
        {tiltAngle > 0 && (
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)'
          }}>
            Tilt: {tiltAngle.toFixed(1)}° {postureState === 'left_lean' ? 'Left' : postureState === 'right_lean' ? 'Right' : ''}
          </div>
        )}
      </div>
    </div>
  );
};

export default PostureVisualization;