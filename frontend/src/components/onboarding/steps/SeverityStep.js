import React from 'react';

const SeverityStep = ({ value, onChange }) => {
  const severityLabels = {
    1: { label: 'Very Mild', description: 'Barely noticeable pushing tendency' },
    2: { label: 'Mild', description: 'Slight pushing, easily correctable' },
    3: { label: 'Moderate', description: 'Noticeable pushing that requires attention' },
    4: { label: 'Severe', description: 'Strong pushing tendency, difficult to correct' },
    5: { label: 'Very Severe', description: 'Intense pushing, requires constant vigilance' }
  };

  const currentLabel = value ? severityLabels[value] : null;

  return (
    <div>
      <h2 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-2)',
        textAlign: 'center'
      }}>
        Pushing Tendency Severity
      </h2>

      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-700)',
        textAlign: 'center',
        marginBottom: 'var(--spacing-6)',
        lineHeight: '1.5'
      }}>
        How would you rate the severity of your pushing tendency toward your affected side?
      </p>

      <div style={{ marginBottom: 'var(--spacing-6)' }}>
        {/* Slider */}
        <div style={{
          position: 'relative',
          marginBottom: 'var(--spacing-4)'
        }}>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            value={value || 3}
            onChange={(e) => onChange(parseInt(e.target.value))}
            style={{
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: `linear-gradient(to right, var(--primary-blue) 0%, var(--primary-blue) ${((value || 3) - 1) * 25}%, var(--gray-200) ${((value || 3) - 1) * 25}%, var(--gray-200) 100%)`,
              outline: 'none',
              appearance: 'none',
              cursor: 'pointer'
            }}
          />
          
          {/* Slider thumb styling */}
          <style>
            {`
              input[type="range"]::-webkit-slider-thumb {
                appearance: none;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: var(--primary-blue);
                cursor: pointer;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
              }
              
              input[type="range"]::-moz-range-thumb {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: var(--primary-blue);
                cursor: pointer;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
              }
            `}
          </style>
        </div>

        {/* Scale Labels */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--gray-500)',
          marginBottom: 'var(--spacing-4)'
        }}>
          <span>1</span>
          <span>2</span>
          <span>3</span>
          <span>4</span>
          <span>5</span>
        </div>

        {/* Current Selection Display */}
        {currentLabel && (
          <div style={{
            padding: 'var(--spacing-4)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--border-radius-md)',
            border: '1px solid var(--primary-blue-200)',
            textAlign: 'center'
          }}>
            <div style={{
              fontSize: 'var(--font-size-base)',
              fontWeight: '600',
              color: 'var(--primary-blue-700)',
              marginBottom: 'var(--spacing-1)'
            }}>
              Level {value}: {currentLabel.label}
            </div>
            <div style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--primary-blue-600)'
            }}>
              {currentLabel.description}
            </div>
          </div>
        )}
      </div>

      <div style={{
        padding: 'var(--spacing-3)',
        backgroundColor: 'var(--gray-50)',
        borderRadius: 'var(--border-radius-md)',
        border: '1px solid var(--gray-200)'
      }}>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--gray-600)',
          margin: 0,
          textAlign: 'center'
        }}>
          This helps us set appropriate alert thresholds for your safety and comfort.
        </p>
      </div>
    </div>
  );
};

export default SeverityStep;