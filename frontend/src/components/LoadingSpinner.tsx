/**
 * Loading Spinner Component
 * Displays a loading indicator
 */

import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="w-8 h-8 border-2 border-foreground border-t-transparent animate-spin mb-4"></div>
      <p className="text-sm text-mutedForeground uppercase tracking-widest">{message}</p>
    </div>
  );
};

export default LoadingSpinner;

