import React from 'react';

const ProgressBar = ({ current, total, color = 'var(--primary-blue)' }) => {
  const percentage = (current / total) * 100;

  return (
    <div style={{
      width: '100%',
      height: '6px',
      backgroundColor: 'var(--gray-200)',
      borderRadius: '3px',
      overflow: 'hidden'
    }}>
      <div
        style={{
          width: `${percentage}%`,
          height: '100%',
          backgroundColor: color,
          borderRadius: '3px',
          transition: 'width 0.3s ease-in-out'
        }}
      />
    </div>
  );
};

export default ProgressBar;