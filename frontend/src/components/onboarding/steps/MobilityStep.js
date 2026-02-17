import React from 'react';

const MobilityStep = ({ value, onChange }) => {
  const mobilityOptions = [
    {
      id: 'wheelchair',
      label: 'Wheelchair',
      description: 'I primarily use a wheelchair for mobility'
    },
    {
      id: 'walker',
      label: 'Walker/Rollator',
      description: 'I use a walker or rollator for support'
    },
    {
      id: 'cane',
      label: 'Cane/Walking Stick',
      description: 'I use a cane or walking stick for balance'
    },
    {
      id: 'independent',
      label: 'Independent Walking',
      description: 'I can walk without mobility aids'
    }
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
        Current Mobility Level
      </h2>

      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-700)',
        textAlign: 'center',
        marginBottom: 'var(--spacing-6)',
        lineHeight: '1.5'
      }}>
        What best describes your current mobility level?
      </p>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-3)'
      }}>
        {mobilityOptions.map((option) => (
          <label
            key={option.id}
            style={{
              display: 'flex',
              alignItems: 'center',
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
              name="mobilityLevel"
              value={option.id}
              checked={value === option.id}
              onChange={(e) => onChange(e.target.value)}
              style={{
                marginRight: 'var(--spacing-3)',
                accentColor: 'var(--primary-blue)'
              }}
            />
            
            <div style={{
              width: '40px',
              height: '40px',
              backgroundColor: value === option.id ? 'var(--primary-blue-100)' : 'var(--gray-100)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 'var(--spacing-3)',
              fontSize: 'var(--font-size-lg)'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                backgroundColor: value === option.id ? 'var(--primary-blue)' : 'var(--gray-400)',
                borderRadius: '50%'
              }} />
            </div>
            
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
          This information helps us adjust sensitivity settings for your specific mobility needs.
        </p>
      </div>
    </div>
  );
};

export default MobilityStep;