/**
 * Error Message Component
 * Displays error messages with optional retry functionality
 */

import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  onRetry, 
  retryLabel = 'Retry' 
}) => {
  return (
    <div className="p-6 border-2 border-foreground bg-background">
      <div className="mb-4">
        <h3 className="text-lg font-display font-bold mb-2 uppercase tracking-widest">
          Error
        </h3>
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

