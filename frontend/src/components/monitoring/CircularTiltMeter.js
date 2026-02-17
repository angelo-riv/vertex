import React from 'react';

const CircularTiltMeter = ({ 
  tiltAngle = 0, 
  direction = 'center', // 'left', 'right', 'center'
  maxAngle = 30,
  size = 100,
  warningThreshold = 8,
  dangerThreshold = 15
}) => {
  // Normalize tilt angle to 0-1 range
  const normalizedAngle = Math.min(Math.abs(tiltAngle), maxAngle) / maxAngle;
  
  // Calculate the arc path for the progress indicator
  const radius = (size - 20) / 2;
  const centerX = size / 2;
  const centerY = size / 2;
  const startAngle = -90; // Start from top
  const endAngle = startAngle + (normalizedAngle * 180); // Half circle for tilt range
  
  // Convert angles to radians
  const startRad = (startAngle * Math.PI) / 180;
  const endRad = (endAngle * Math.PI) / 180;
  
  // Calculate arc path
  const startX = centerX + radius * Math.cos(startRad);
  const startY = centerY + radius * Math.sin(startRad);
  const endX = centerX + radius * Math.cos(endRad);
  const endY = centerY + radius * Math.sin(endRad);
  
  const largeArcFlag = normalizedAngle > 0.5 ? 1 : 0;
  
  const arcPath = `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY}`;
  
  // Determine color based on tilt angle and thresholds
  const getTiltColor = () => {
    const absAngle = Math.abs(tiltAngle);
    if (absAngle >= dangerThreshold) {
      return '#dc2626'; // Red for danger
    } else if (absAngle >= warningThreshold) {
      return '#f59e0b'; // Amber for warning
    } else {
      return 'var(--primary-blue)'; // Blue for safe
    }
  };
  
  const tiltColor = getTiltColor();
  
  // Get status text
  const getStatusText = () => {
    const absAngle = Math.abs(tiltAngle);
    if (absAngle >= dangerThreshold) {
      return 'Unsafe';
    } else if (absAngle >= warningThreshold) {
      return 'Warning';
    } else {
      return 'Safe';
    }
  };
  
  // Direction indicator
  const getDirectionIndicator = () => {
    if (direction === 'left') {
      return '←';
    } else if (direction === 'right') {
      return '→';
    } else {
      return '↑';
    }
  };

  return (
    <div 
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 'var(--spacing-2)'
      }}
      role="meter"
      aria-valuemin="0"
      aria-valuemax={maxAngle}
      aria-valuenow={Math.abs(tiltAngle)}
      aria-label={`Tilt meter showing ${Math.abs(tiltAngle).toFixed(1)} degrees ${direction}`}
    >
      {/* Circular Gauge */}
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
            transform: 'rotate(-90deg)', // Rotate so 0 degrees is at top
            transition: 'all 300ms ease-in-out'
          }}
        >
          {/* Background Circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="none"
            stroke="var(--gray-200)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          
          {/* Warning Threshold Arc */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="none"
            stroke="#fde68a"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(warningThreshold / maxAngle) * Math.PI * radius} ${Math.PI * radius * 2}`}
            opacity="0.3"
          />
          
          {/* Danger Threshold Arc */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="none"
            stroke="#fecaca"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(dangerThreshold / maxAngle) * Math.PI * radius} ${Math.PI * radius * 2}`}
            opacity="0.3"
          />
          
          {/* Progress Arc */}
          {normalizedAngle > 0 && (
            <circle
              cx={centerX}
              cy={centerY}
              r={radius}
              fill="none"
              stroke={tiltColor}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${normalizedAngle * Math.PI * radius} ${Math.PI * radius * 2}`}
              style={{
                transition: 'stroke-dasharray 300ms ease-in-out, stroke 300ms ease-in-out'
              }}
            />
          )}
          
          {/* Center Dot */}
          <circle
            cx={centerX}
            cy={centerY}
            r="4"
            fill={tiltColor}
            style={{
              transition: 'fill 300ms ease-in-out'
            }}
          />
        </svg>
        
        {/* Center Content */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          pointerEvents: 'none'
        }}>
          {/* Tilt Angle */}
          <div style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '700',
            color: tiltColor,
            lineHeight: '1',
            transition: 'color 300ms ease-in-out'
          }}>
            {Math.abs(tiltAngle).toFixed(1)}°
          </div>
          
          {/* Direction Indicator */}
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)',
            marginTop: '2px'
          }}>
            {getDirectionIndicator()}
          </div>
        </div>
        
        {/* Threshold Markers */}
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px'
        }}>
          {/* Warning Marker */}
          <div style={{
            width: '8px',
            height: '3px',
            backgroundColor: '#f59e0b',
            borderRadius: '2px',
            opacity: 0.6
          }} />
          {/* Danger Marker */}
          <div style={{
            width: '8px',
            height: '3px',
            backgroundColor: '#dc2626',
            borderRadius: '2px',
            opacity: 0.6
          }} />
        </div>
      </div>
      
      {/* Status Text */}
      <div style={{
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: 'var(--font-size-sm)',
          fontWeight: '600',
          color: tiltColor,
          transition: 'color 300ms ease-in-out'
        }}>
          {getStatusText()}
        </div>
        
        {direction !== 'center' && (
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--gray-600)',
            marginTop: 'var(--spacing-1)'
          }}>
            {direction === 'left' ? 'Leaning Left' : 'Leaning Right'}
          </div>
        )}
      </div>
      
      {/* Threshold Legend */}
      <div style={{
        display: 'flex',
        gap: 'var(--spacing-3)',
        fontSize: 'var(--font-size-xs)',
        color: 'var(--gray-500)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
          <div style={{
            width: '8px',
            height: '3px',
            backgroundColor: '#f59e0b',
            borderRadius: '2px'
          }} />
          <span>{warningThreshold}°</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
          <div style={{
            width: '8px',
            height: '3px',
            backgroundColor: '#dc2626',
            borderRadius: '2px'
          }} />
          <span>{dangerThreshold}°</span>
        </div>
      </div>
    </div>
  );
};

export default CircularTiltMeter;