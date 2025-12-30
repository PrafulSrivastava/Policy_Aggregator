/**
 * Error Message Component
 * Displays error messages with optional retry functionality
 */

import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  onClose?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  onRetry, 
  retryLabel = 'Retry',
  onClose
}) => {
  return (
    <div className="p-6 border-2 border-foreground bg-background">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-display font-bold uppercase tracking-widest">
            Error
          </h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-foreground hover:underline text-lg font-bold"
              aria-label="Close error message"
            >
              ×
            </button>
          )}
        </div>
        <p className="text-sm text-mutedForeground">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn-primary"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;

