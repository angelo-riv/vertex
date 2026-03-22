import React, { memo } from 'react';

const CircularTiltMeter = ({
  tiltAngle = 0,
  direction = 'center', // 'left', 'right', 'center'
  maxAngle = 30,
  size = 100,
  warningThreshold = 8,
  dangerThreshold = 15,
  // New clinical threshold props
  clinicalThresholds = { normal: 5, pusher: 10, severe: 20 },
  calibratedBaseline = 0,
  showClinicalMarkers = true
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

  // Determine color based on tilt angle and thresholds (enhanced with clinical thresholds)
  const getTiltColor = () => {
    const absAngle = Math.abs(tiltAngle);

    // Use clinical thresholds if available and enabled
    if (showClinicalMarkers) {
      if (absAngle >= clinicalThresholds.severe) {
        return '#dc2626'; // Red for severe clinical threshold
      } else if (absAngle >= clinicalThresholds.pusher) {
        return '#f59e0b'; // Amber for pusher threshold
      } else if (absAngle >= clinicalThresholds.normal) {
        return '#fbbf24'; // Yellow for normal threshold
      } else {
        return 'var(--primary-blue)'; // Blue for safe
      }
    }

    // Fallback to original thresholds
    if (absAngle >= dangerThreshold) {
      return '#dc2626'; // Red for danger
    } else if (absAngle >= warningThreshold) {
      return '#f59e0b'; // Amber for warning
    } else {
      return 'var(--primary-blue)'; // Blue for safe
    }
  };

  const tiltColor = getTiltColor();

  // Get status text (enhanced with clinical status)
  const getStatusText = () => {
    const absAngle = Math.abs(tiltAngle);

    if (showClinicalMarkers) {
      if (absAngle >= clinicalThresholds.severe) {
        return 'Severe Lean';
      } else if (absAngle >= clinicalThresholds.pusher) {
        return 'Pusher Range';
      } else if (absAngle >= clinicalThresholds.normal) {
        return 'Mild Lean';
      } else {
        return 'Normal';
      }
    }

    // Fallback to original status
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

  // Calculate clinical threshold positions on the circle
  const getThresholdArcLength = (thresholdAngle) => {
    const normalizedThreshold = Math.min(thresholdAngle, maxAngle) / maxAngle;
    return normalizedThreshold * Math.PI * radius;
  };

  // Render clinical threshold markers
  const renderClinicalThresholds = () => {
    if (!showClinicalMarkers) return null;

    return (
      <>
        {/* Normal threshold (5°) - Light yellow */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="#fbbf24"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={`${getThresholdArcLength(clinicalThresholds.normal)} ${Math.PI * radius * 2}`}
          opacity="0.4"
        />

        {/* Pusher threshold (10°) - Orange */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="#f59e0b"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={`${getThresholdArcLength(clinicalThresholds.pusher)} ${Math.PI * radius * 2}`}
          opacity="0.5"
        />

        {/* Severe threshold (20°) - Red */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="#dc2626"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={`${getThresholdArcLength(clinicalThresholds.severe)} ${Math.PI * radius * 2}`}
          opacity="0.6"
        />
      </>
    );
  };

  // Render calibrated baseline indicator
  const renderBaselineIndicator = () => {
    if (!showClinicalMarkers || calibratedBaseline === 0) return null;

    // Calculate baseline position
    const baselineNormalized = Math.min(Math.abs(calibratedBaseline), maxAngle) / maxAngle;
    const baselineAngle = -90 + (baselineNormalized * 180);
    const baselineRad = (baselineAngle * Math.PI) / 180;
    const baselineX = centerX + (radius - 5) * Math.cos(baselineRad);
    const baselineY = centerY + (radius - 5) * Math.sin(baselineRad);

    return (
      <>
        {/* Baseline marker */}
        <circle
          cx={baselineX}
          cy={baselineY}
          r="3"
          fill="#10b981"
          stroke="#ffffff"
          strokeWidth="1"
        />
        {/* Baseline label */}
        <text
          x={baselineX}
          y={baselineY - 8}
          textAnchor="middle"
          fontSize="8"
          fill="#10b981"
          fontWeight="600"
        >
          B
        </text>
      </>
    );
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

          {/* Clinical Threshold Markers */}
          {renderClinicalThresholds()}

          {/* Original Warning Threshold Arc (shown when clinical markers are disabled) */}
          {!showClinicalMarkers && (
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
          )}

          {/* Original Danger Threshold Arc (shown when clinical markers are disabled) */}
          {!showClinicalMarkers && (
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
          )}

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
                transition: 'stroke-dasharray 100ms ease-out, stroke 100ms ease-out' // Optimized for real-time updates
              }}
            />
          )}

          {/* Calibrated Baseline Indicator */}
          {renderBaselineIndicator()}

          {/* Center Dot */}
          <circle
            cx={centerX}
            cy={centerY}
            r="4"
            fill={tiltColor}
            style={{
              transition: 'fill 100ms ease-out' // Faster transition for real-time updates
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
            transition: 'color 100ms ease-out' // Faster transition for real-time updates
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
          {showClinicalMarkers ? (
            <>
              {/* Clinical Markers */}
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#fbbf24',
                borderRadius: '1px',
                opacity: 0.6
              }} />
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#f59e0b',
                borderRadius: '1px',
                opacity: 0.6
              }} />
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#dc2626',
                borderRadius: '1px',
                opacity: 0.6
              }} />
              {calibratedBaseline !== 0 && (
                <div style={{
                  width: '8px',
                  height: '2px',
                  backgroundColor: '#10b981',
                  borderRadius: '1px',
                  opacity: 0.8
                }} />
              )}
            </>
          ) : (
            <>
              {/* Original Markers */}
              <div style={{
                width: '8px',
                height: '3px',
                backgroundColor: '#f59e0b',
                borderRadius: '2px',
                opacity: 0.6
              }} />
              <div style={{
                width: '8px',
                height: '3px',
                backgroundColor: '#dc2626',
                borderRadius: '2px',
                opacity: 0.6
              }} />
            </>
          )}
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
          transition: 'color 100ms ease-out' // Faster transition for real-time updates
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
        color: 'var(--gray-500)',
        flexWrap: 'wrap',
        justifyContent: 'center'
      }}>
        {showClinicalMarkers ? (
          <>
            {/* Clinical Threshold Legend */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#fbbf24',
                borderRadius: '1px'
              }} />
              <span>{clinicalThresholds.normal}°</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#f59e0b',
                borderRadius: '1px'
              }} />
              <span>{clinicalThresholds.pusher}°</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
              <div style={{
                width: '8px',
                height: '2px',
                backgroundColor: '#dc2626',
                borderRadius: '1px'
              }} />
              <span>{clinicalThresholds.severe}°</span>
            </div>
            {calibratedBaseline !== 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-1)' }}>
                <div style={{
                  width: '8px',
                  height: '2px',
                  backgroundColor: '#10b981',
                  borderRadius: '1px'
                }} />
                <span>Baseline</span>
              </div>
            )}
          </>
        ) : (
          <>
            {/* Original Threshold Legend */}
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
          </>
        )}
      </div>
    </div>
  );
};

export default memo(CircularTiltMeter);