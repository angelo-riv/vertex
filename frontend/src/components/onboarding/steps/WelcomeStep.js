import React from 'react';

const WelcomeStep = () => {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: '80px',
        height: '80px',
        backgroundColor: 'var(--primary-blue-100)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto var(--spacing-6) auto'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          backgroundColor: 'var(--primary-blue)',
          borderRadius: '50%'
        }} />
      </div>

      <h2 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        color: 'var(--gray-900)',
        marginBottom: 'var(--spacing-4)'
      }}>
        Welcome to Vertex
      </h2>

      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-700)',
        lineHeight: '1.6',
        marginBottom: 'var(--spacing-4)'
      }}>
        We'll help you set up your personalized rehabilitation program. This assessment takes about 2 minutes and will configure your device for optimal results.
      </p>

      <div style={{
        backgroundColor: 'var(--primary-blue-50)',
        padding: 'var(--spacing-4)',
        borderRadius: 'var(--border-radius-md)',
        border: '1px solid var(--primary-blue-200)'
      }}>
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--primary-blue-700)',
          margin: 0,
          fontWeight: '500'
        }}>
          Your responses will help us create a safe and effective therapy plan tailored to your specific needs.
        </p>
      </div>
    </div>
  );
};

export default WelcomeStep;