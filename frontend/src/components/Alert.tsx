/**
 * Alert Component
 * Displays error or informational messages with design system styling
 */

import React from 'react';

export type AlertType = 'error' | 'success' | 'info' | 'warning';

interface AlertProps {
  type?: AlertType;
  message: string;
  onClose?: () => void;
}

const Alert: React.FC<AlertProps> = ({ type = 'error', message, onClose }) => {
  const baseStyles = 'p-4 border-2 mb-6';
  
  const typeStyles = {
    error: 'bg-background text-foreground border-foreground',
    success: 'bg-background text-foreground border-foreground',
    info: 'bg-background text-foreground border-foreground',
    warning: 'bg-background text-foreground border-foreground',
  };

  return (
    <div className={`${baseStyles} ${typeStyles[type]}`} role="alert">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">{message}</p>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-4 text-foreground hover:underline"
            aria-label="Close alert"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default Alert;

