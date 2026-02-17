import React from 'react';

const LoadingScreen = () => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--primary-blue-50)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column'
    }}>
      {/* Logo */}
      <div style={{
        width: '80px',
        height: '80px',
        backgroundColor: 'var(--primary-blue)',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 'var(--spacing-6)',
        animation: 'pulse 2s infinite'
      }}>
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" fill="white"/>
        </svg>
      </div>

      {/* Loading Spinner */}
      <div style={{
        width: '32px',
        height: '32px',
        border: '3px solid var(--primary-blue-200)',
        borderTop: '3px solid var(--primary-blue)',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        marginBottom: 'var(--spacing-4)'
      }} />

      {/* Loading Text */}
      <p style={{
        fontSize: 'var(--font-size-base)',
        color: 'var(--gray-600)',
        textAlign: 'center'
      }}>
        Loading...
      </p>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.05); opacity: 0.8; }
        }
      `}</style>
    </div>
  );
};

export default LoadingScreen;