import React from 'react';

const StrokeSideStep = ({ value, onChange }) => {
  const options = [
    { id: 'left', label: 'Left side', description: 'Stroke affected my left side' },
    { id: 'right', label: 'Right side', description: 'Stroke affected my right side' },
    { id: 'both', label: 'Both sides', description: 'Stroke affected both sides' },
    { id: 'not_sure', label: 'Not sure', description: 'I\'m not certain which side was affected' }
  ];

  return (
    <div>
      <h2 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-2)',
        textAlign: 'center'
      }}>
        Stroke Side Assessment
      </h2>

      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-700)',
        textAlign: 'center',
        marginBottom: 'var(--spacing-6)',
        lineHeight: '1.5'
      }}>
        Which side of your body was primarily affected by your stroke?
      </p>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-3)'
      }}>
        {options.map((option) => (
          <label
            key={option.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              padding: 'var(--spacing-4)',
              border: `2px solid ${value === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
              borderRadius: 'var(--border-radius-md)',
              backgroundColor: value === option.id ? 'var(--primary-blue-50)' : 'white',
              cursor: 'pointer',
              transition: 'var(--transition-fast)'
            }}
          >
            <input
              type="radio"
              name="strokeSide"
              value={option.id}
              checked={value === option.id}
              onChange={(e) => onChange(e.target.value)}
              style={{
                marginRight: 'var(--spacing-3)',
                marginTop: '2px',
                accentColor: 'var(--primary-blue)'
              }}
            />
            <div>
              <div style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: '500',
                color: 'var(--gray-900)',
                marginBottom: 'var(--spacing-1)'
              }}>
                {option.label}
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)'
              }}>
                {option.description}
              </div>
            </div>
          </label>
        ))}
      </div>

      <div style={{
        marginTop: 'var(--spacing-4)',
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
          This information helps us configure your device's sensitivity and feedback patterns.
        </p>
      </div>
    </div>
  );
};

export default StrokeSideStep;