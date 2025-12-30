/**
 * Status Badge Component
 * Color-coded status indicator for source health
 */

import React from 'react';

export type SourceStatus = 'healthy' | 'stale' | 'error' | 'never_checked';

interface StatusBadgeProps {
  status: SourceStatus;
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusConfig = (status: SourceStatus) => {
    switch (status) {
      case 'healthy':
        return {
          label: 'Healthy',
          bgColor: 'bg-green-500',
          textColor: 'text-white',
        };
      case 'stale':
        return {
          label: 'Stale',
          bgColor: 'bg-yellow-500',
          textColor: 'text-black',
        };
      case 'error':
        return {
          label: 'Error',
          bgColor: 'bg-red-500',
          textColor: 'text-white',
        };
      case 'never_checked':
        return {
          label: 'Never Checked',
          bgColor: 'bg-gray-400',
          textColor: 'text-white',
        };
      default:
        return {
          label: 'Unknown',
          bgColor: 'bg-gray-400',
          textColor: 'text-white',
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span
      className={`inline-flex items-center px-2 py-1 text-xs font-semibold ${config.bgColor} ${config.textColor} ${className}`}
      role="status"
      aria-label={`Source status: ${config.label}`}
    >
      {config.label}
    </span>
  );
};

export default StatusBadge;

