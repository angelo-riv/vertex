import React from 'react';
import PostureVisualization from '../components/monitoring/PostureVisualization';

const HomePage = () => {
  // Get user info from localStorage for demo
  const userEmail = localStorage.getItem('currentUserEmail') || 'test@example.com';
  const userName = userEmail.split('@')[0]; // Simple name extraction for demo

  return (
    <div style={{
      padding: 'var(--spacing-4)',
      maxWidth: '1200px',
      margin: '0 auto',
      minHeight: 'calc(100vh - 160px)' // Account for header and bottom nav
    }}>
      {/* Welcome Section */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--gray-100)'
      }}>
        <h2 style={{
          fontSize: 'var(--font-size-2xl)',
          fontWeight: '700',
          color: 'var(--gray-900)',
          marginBottom: 'var(--spacing-2)',
          letterSpacing: '-0.025em'
        }}>
          Welcome back, {userName}
        </h2>
        <p style={{
          fontSize: 'var(--font-size-lg)',
          color: 'var(--gray-600)',
          lineHeight: '1.6',
          margin: 0
        }}>
          Your rehabilitation dashboard is ready. Monitor your progress and stay on track with your therapy goals.
        </p>
      </div>

      {/* Main Content Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: 'var(--spacing-6)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Quick Stats */}
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
            Today's Progress
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: 'var(--spacing-4)'
          }}>
            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: 'var(--primary-blue-50)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--primary-blue-100)'
            }}>
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
                Sessions Today
              </div>
            </div>

            <div style={{
              textAlign: 'center',
              padding: 'var(--spacing-4)',
              backgroundColor: 'var(--success-green)'.replace('var(--success-green)', '#F0FDF4'),
              borderRadius: 'var(--radius-md)',
              border: '1px solid #BBF7D0'
            }}>
              <div style={{
                fontSize: '2rem',
                fontWeight: '700',
                color: 'var(--success-green)',
                marginBottom: 'var(--spacing-1)'
              }}>
                --
              </div>
              <div style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-600)',
                fontWeight: '500'
              }}>
                Upright Time
              </div>
            </div>
          </div>
        </div>

        {/* Current Status */}
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
            Current Status
          </h3>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--spacing-8)',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--radius-lg)',
            border: '2px dashed var(--gray-200)',
            minHeight: '200px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <PostureVisualization 
                postureState="upright" 
                tiltAngle={0}
                size={120}
              />
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-500)',
                margin: 'var(--spacing-4) 0 0 0',
                fontWeight: '500'
              }}>
                Connect your device to start monitoring
              </p>
              <p style={{
                fontSize: 'var(--font-size-sm)',
                color: 'var(--gray-400)',
                margin: 'var(--spacing-1) 0 0 0'
              }}>
                Device status: Disconnected
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Action Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 'var(--spacing-4)',
        marginBottom: 'var(--spacing-6)'
      }}>
        {/* Quick Actions */}
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
              <polyline points="12,6 12,12 16,14"/>
            </svg>
            Quick Actions
          </h3>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--spacing-3)'
          }}>
            <button className="btn btn-primary" style={{ 
              width: '100%',
              padding: 'var(--spacing-4)',
              fontSize: 'var(--font-size-base)',
              fontWeight: '600'
            }}>
              Start New Session
            </button>
            <button className="btn btn-secondary" style={{ 
              width: '100%',
              padding: 'var(--spacing-3)',
              fontSize: 'var(--font-size-sm)'
            }}>
              View Progress
            </button>
            <button className="btn btn-secondary" style={{ 
              width: '100%',
              padding: 'var(--spacing-3)',
              fontSize: 'var(--font-size-sm)'
            }}>
              Device Settings
            </button>
          </div>
        </div>

        {/* Recent Activity */}
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
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
            Recent Activity
          </h3>

          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-8)',
            color: 'var(--gray-500)'
          }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" style={{ marginBottom: 'var(--spacing-3)', opacity: 0.5 }}>
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            <p style={{
              fontSize: 'var(--font-size-base)',
              margin: 0,
              fontWeight: '500'
            }}>
              No recent activity
            </p>
            <p style={{
              fontSize: 'var(--font-size-sm)',
              margin: 'var(--spacing-1) 0 0 0',
              color: 'var(--gray-400)'
            }}>
              Start your first session to see activity here
            </p>
          </div>
        </div>
      </div>

      {/* Demo Success Message */}
      <div style={{
        backgroundColor: 'var(--primary-blue-50)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-6)',
        border: '1px solid var(--primary-blue-200)',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--spacing-2)',
          marginBottom: 'var(--spacing-2)'
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary-blue)" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22,4 12,14.01 9,11.01"/>
          </svg>
          <h4 style={{
            fontSize: 'var(--font-size-lg)',
            fontWeight: '600',
            color: 'var(--primary-blue)',
            margin: 0
          }}>
            Dashboard Ready!
          </h4>
        </div>
        <p style={{
          fontSize: 'var(--font-size-base)',
          color: 'var(--primary-blue)',
          margin: 0,
          opacity: 0.8
        }}>
          You've successfully completed the onboarding flow. The Vertex rehabilitation dashboard is now ready for use.
        </p>
      </div>
    </div>
  );
};

export default HomePage;