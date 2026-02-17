import React from 'react';

const TimelineStep = ({ 
  strokeTimeline, 
  therapyStatus, 
  onStrokeTimelineChange, 
  onTherapyStatusChange 
}) => {
  const timelineOptions = [
    { id: 'recent', label: 'Less than 3 months ago', description: 'Recent stroke, early recovery phase' },
    { id: 'moderate', label: '3-12 months ago', description: 'Active recovery and rehabilitation phase' },
    { id: 'extended', label: '1-2 years ago', description: 'Ongoing rehabilitation and adaptation' },
    { id: 'chronic', label: 'More than 2 years ago', description: 'Chronic phase, maintenance therapy' }
  ];

  const therapyOptions = [
    { id: 'active', label: 'Currently in therapy', description: 'Receiving regular physical or occupational therapy' },
    { id: 'intermittent', label: 'Occasional therapy', description: 'Periodic therapy sessions or check-ups' },
    { id: 'completed', label: 'Completed formal therapy', description: 'Finished structured rehabilitation program' },
    { id: 'none', label: 'No formal therapy', description: 'Not currently receiving professional therapy' }
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
        Stroke Timeline & Therapy
      </h2>

      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-700)',
        textAlign: 'center',
        marginBottom: 'var(--spacing-6)',
        lineHeight: '1.5'
      }}>
        Help us understand your recovery timeline and current therapy status.
      </p>

      {/* Stroke Timeline Section */}
      <div style={{ marginBottom: 'var(--spacing-6)' }}>
        <h3 style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: 'var(--gray-800)',
          marginBottom: 'var(--spacing-3)'
        }}>
          When did your stroke occur?
        </h3>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-2)'
        }}>
          {timelineOptions.map((option) => (
            <label
              key={option.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                padding: 'var(--spacing-3)',
                border: `2px solid ${strokeTimeline === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
                borderRadius: 'var(--border-radius-md)',
                backgroundColor: strokeTimeline === option.id ? 'var(--primary-blue-50)' : 'white',
                cursor: 'pointer',
                transition: 'var(--transition-fast)'
              }}
            >
              <input
                type="radio"
                name="strokeTimeline"
                value={option.id}
                checked={strokeTimeline === option.id}
                onChange={(e) => onStrokeTimelineChange(e.target.value)}
                style={{
                  marginRight: 'var(--spacing-3)',
                  marginTop: '2px',
                  accentColor: 'var(--primary-blue)'
                }}
              />
              <div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '500',
                  color: 'var(--gray-900)',
                  marginBottom: 'var(--spacing-1)'
                }}>
                  {option.label}
                </div>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--gray-600)'
                }}>
                  {option.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Therapy Status Section */}
      <div>
        <h3 style={{
          fontSize: 'var(--font-size-base)',
          fontWeight: '600',
          color: 'var(--gray-800)',
          marginBottom: 'var(--spacing-3)'
        }}>
          What is your current therapy status?
        </h3>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--spacing-2)'
        }}>
          {therapyOptions.map((option) => (
            <label
              key={option.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                padding: 'var(--spacing-3)',
                border: `2px solid ${therapyStatus === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
                borderRadius: 'var(--border-radius-md)',
                backgroundColor: therapyStatus === option.id ? 'var(--primary-blue-50)' : 'white',
                cursor: 'pointer',
                transition: 'var(--transition-fast)'
              }}
            >
              <input
                type="radio"
                name="therapyStatus"
                value={option.id}
                checked={therapyStatus === option.id}
                onChange={(e) => onTherapyStatusChange(e.target.value)}
                style={{
                  marginRight: 'var(--spacing-3)',
                  marginTop: '2px',
                  accentColor: 'var(--primary-blue)'
                }}
              />
              <div>
                <div style={{
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: '500',
                  color: 'var(--gray-900)',
                  marginBottom: 'var(--spacing-1)'
                }}>
                  {option.label}
                </div>
                <div style={{
                  fontSize: 'var(--font-size-xs)',
                  color: 'var(--gray-600)'
                }}>
                  {option.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div style={{
        marginTop: 'var(--spacing-4)',
        padding: 'var(--spacing-3)',
        backgroundColor: 'var(--primary-blue-50)',
        borderRadius: 'var(--border-radius-md)',
        border: '1px solid var(--primary-blue-200)'
      }}>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--primary-blue-700)',
          margin: 0,
          textAlign: 'center',
          fontWeight: '500'
        }}>
          This information helps us create a personalized rehabilitation plan that complements your current therapy.
        </p>
      </div>
    </div>
  );
};

export default TimelineStep;