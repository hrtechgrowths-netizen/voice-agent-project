import React from 'react';

interface ProgressBarProps {
  progress: number;
  statusText: string;
  visible: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, statusText, visible }) => {
  if (!visible) return null;
  
  return (
    <div style={{
      width: '100%',
      background: 'rgba(255, 255, 255, 0.02)',
      border: '1px solid var(--glass-border)',
      padding: '12px',
      borderRadius: '8px',
      marginTop: '12px',
      boxSizing: 'border-box'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '12px' }}>
        <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{statusText}</span>
        <span style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>{Math.round(progress)}%</span>
      </div>
      <div style={{
        width: '100%',
        height: '4px',
        background: 'var(--bg-tertiary)',
        borderRadius: '2px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          background: 'var(--accent-gradient)',
          borderRadius: '2px',
          transition: 'width 0.1s ease-out'
        }} />
      </div>
    </div>
  );
};
