import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--primary-blue-50)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--spacing-4)'
    }}>
      <div className="container" style={{ maxWidth: '400px' }}>
        <div className="card">
          {/* Header with Logo */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-8)' }}>
            <div style={{
              width: '80px',
              height: '80px',
              backgroundColor: 'var(--primary-blue)',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto var(--spacing-4)'
            }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="white"/>
              </svg>
            </div>
            <h1 style={{
              fontSize: 'var(--font-size-2xl)',
              fontWeight: '600',
              color: 'var(--gray-900)',
              marginBottom: 'var(--spacing-2)'
            }}>
              Vertex
            </h1>
            <p style={{
              fontSize: 'var(--font-size-base)',
              color: 'var(--gray-600)',
              lineHeight: '1.5'
            }}>
              Supporting your journey to better balance and posture awareness
            </p>
          </div>

          {/* Features List */}
          <div style={{ marginBottom: 'var(--spacing-8)' }}>
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: 'var(--spacing-4)'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: 'var(--primary-blue)',
                borderRadius: '50%',
                marginTop: '8px',
                marginRight: 'var(--spacing-3)',
                flexShrink: 0
              }} />
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-700)',
                margin: 0,
                lineHeight: '1.5'
              }}>
                Real-time posture monitoring with gentle haptic guidance
              </p>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: 'var(--spacing-4)'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: 'var(--primary-blue)',
                borderRadius: '50%',
                marginTop: '8px',
                marginRight: 'var(--spacing-3)',
                flexShrink: 0
              }} />
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-700)',
                margin: 0,
                lineHeight: '1.5'
              }}>
                Track your progress with clear, meaningful insights
              </p>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              marginBottom: 'var(--spacing-4)'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: 'var(--primary-blue)',
                borderRadius: '50%',
                marginTop: '8px',
                marginRight: 'var(--spacing-3)',
                flexShrink: 0
              }} />
              <p style={{
                fontSize: 'var(--font-size-base)',
                color: 'var(--gray-700)',
                margin: 0,
                lineHeight: '1.5'
              }}>
                Personalized support for pusher syndrome rehabilitation
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ marginBottom: 'var(--spacing-6)' }}>
            <Link
              to="/auth/signup"
              className="btn btn-primary"
              style={{
                width: '100%',
                marginBottom: 'var(--spacing-3)',
                textDecoration: 'none',
                display: 'inline-block',
                textAlign: 'center'
              }}
            >
              Create Account
            </Link>

            <Link
              to="/auth/login"
              className="btn btn-secondary"
              style={{
                width: '100%',
                textDecoration: 'none',
                display: 'inline-block',
                textAlign: 'center'
              }}
            >
              Log In
            </Link>
          </div>

          {/* Medical Disclaimer */}
          <div style={{
            textAlign: 'center',
            padding: 'var(--spacing-4)',
            backgroundColor: 'var(--gray-50)',
            borderRadius: 'var(--border-radius-md)'
          }}>
            <p style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--gray-500)',
              lineHeight: '1.4',
              margin: 0
            }}>
              Medical device for rehabilitation use. Consult your healthcare provider.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;