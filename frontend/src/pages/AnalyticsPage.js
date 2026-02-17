import React, { useState } from 'react';

const AnalyticsPage = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('7days');

  const timeframeOptions = [
    { id: '1hour', label: '1 Hour' },
    { id: '24hours', label: '24 Hours' },
    { id: '7days', label: '7 Days' },
    { id: '1month', label: '1 Month' }
  ];

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '1200px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 160px)'
    }}>
      {/* Header */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--spacing-4)',
          marginBottom: 'var(--spacing-4)'
        }}>
          <div>
            <h2 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: '700',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)',
              letterSpacing: '-0.025em',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
              </svg>
              Progress Analytics
            </h2>
            <p style={{
              fontSize: 'var(--font-size-lg)',
              color: 'var(--gray-600)',
              margin: 0
            }}>
              Track your rehabilitation progress and insights
            </p>
          </div>
        </div>

        {/* Timeframe Selector */}
        <div style={{
          display: 'flex',
          gap: 'var(--spacing-2)',
          flexWrap: 'wrap'
        }}>
          {timeframeOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => setSelectedTimeframe(option.id)}
              style={{
                padding: 'var(--spacing-3) var(--spacing-4)',
                border: `2px solid ${selectedTimeframe === option.id ? 'var(--primary-blue)' : 'var(--gray-200)'}`,
                borderRadius: 'var(--radius-md)',
                backgroundColor: selectedTimeframe === option.id ? 'var(--primary-blue-50)' : 'white',
                color: selectedTimeframe === option.id ? 'var(--primary-blue)' : 'var(--gray-700)',
                fontSize: 'var(--font-size-sm)',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'var(--transition-fast)',
                minWidth: '80px'
              }}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-6)'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-5)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 'var(--spacing-3)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: 'var(--primary-blue)',
            marginBottom: 'var(--spacing-1)'
          }}>
            0
          </div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)',
            fontWeight: '500'
          }}>
            Total Sessions
          </div>
        </div>

        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-5)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 'var(--spacing-3)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--success-green)" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22,4 12,14.01 9,11.01"/>
            </svg>
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: 'var(--success-green)',
            marginBottom: 'var(--spacing-1)'
          }}>
            --%
          </div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)',
            fontWeight: '500'
          }}>
            Avg Upright Time
          </div>
        </div>

        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-5)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 'var(--spacing-3)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--warning-orange)" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: 'var(--warning-orange)',
            marginBottom: 'var(--spacing-1)'
          }}>
            --°
          </div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)',
            fontWeight: '500'
          }}>
            Average Tilt
          </div>
        </div>

        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-5)',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 'var(--spacing-3)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--gray-600)" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: '700',
            color: 'var(--gray-600)',
            marginBottom: 'var(--spacing-1)'
          }}>
            --
          </div>
          <div style={{
            fontSize: 'var(--font-size-sm)',
            color: 'var(--gray-600)',
            fontWeight: '500'
          }}>
            Improvement Score
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Upright Time Trends */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
            </svg>
            Upright Time Trends
          </h3>

          <div style={{
            height: '250px',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px dashed var(--gray-200)'
          }}>
            <div style={{ textAlign: 'center' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="1" style={{ marginBottom: 'var(--spacing-3)' }}>
                <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
              </svg>
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-600)',
                margin: 0,
                fontWeight: '500'
              }}>
                Progress Chart
              </p>
              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-400)',
                margin: 'var(--spacing-1) 0 0 0'
              }}>
                Start sessions to see trends
              </p>
            </div>
          </div>
        </div>

        {/* Posture Distribution */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--spacing-6)',
          boxShadow: 'var(--shadow-sm)',
          border: '1px solid var(--gray-100)'
        }}>
          <h3 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--gray-900)',
            marginBottom: 'var(--spacing-4)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            Posture Distribution
          </h3>

          <div style={{
            height: '250px',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px dashed var(--gray-200)'
          }}>
            <div style={{ textAlign: 'center' }}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="1" style={{ marginBottom: 'var(--spacing-3)' }}>
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-600)',
                margin: 0,
                fontWeight: '500'
              }}>
                Posture Analysis
              </p>
              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-400)',
                margin: 'var(--spacing-1) 0 0 0'
              }}>
                Data will appear after sessions
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Insights */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)',
        marginBottom: 'var(--spacing-6)'
      }}>
        <h3 style={{
          fontSize: 'var(--font-size-lg)',
          fontWeight: '600',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-4)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-2)'
        }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Progress Insights
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 'var(--spacing-4)'
        }}>
          <div style={{
            padding: 'var(--spacing-4)',
            backgroundColor: 'var(--primary-blue-50)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--primary-blue-200)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)',
              marginBottom: 'var(--spacing-2)'
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22,4 12,14.01 9,11.01"/>
              </svg>
              <h4 style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: '600',
                color: 'var(--primary-blue)',
                margin: 0
              }}>
                Getting Started
              </h4>
            </div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--primary-blue)',
              margin: 0,
              opacity: 0.8,
              lineHeight: '1.5'
            }}>
              Start your first session to begin tracking your rehabilitation progress. 
              Your personalized insights will appear here as you use the device.
            </p>
          </div>

          <div style={{
            padding: 'var(--spacing-4)',
            backgroundColor: '#F0FDF4',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid #BBF7D0'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-2)',
              marginBottom: 'var(--spacing-2)'
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success-green)" strokeWidth="2">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                <polyline points="9,22 9,12 15,12 15,22"/>
              </svg>
              <h4 style={{
                fontSize: 'var(--font-size-base)',
                fontWeight: '600',
                color: 'var(--success-green)',
                margin: 0
              }}>
                Rehabilitation Goals
              </h4>
            </div>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--success-green)',
              margin: 0,
              opacity: 0.8,
              lineHeight: '1.5'
            }}>
              Track your progress toward improved posture control and reduced 
              pusher syndrome symptoms through consistent monitoring.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;