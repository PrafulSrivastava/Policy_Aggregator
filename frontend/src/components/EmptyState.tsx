/**
 * Empty State Component
 * Displays a message when there's no data to show
 */

import React from 'react';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title: string;
  message?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  actionLabel,
  actionHref,
  onAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h2 className="text-4xl font-display font-bold mb-4 tracking-tight">
        {title}
      </h2>
      {message && (
        <p className="text-lg font-body text-mutedForeground mb-8 max-w-md">
          {message}
        </p>
      )}
      {(actionLabel && (actionHref || onAction)) && (
        <div>
          {actionHref ? (
            <Link to={actionHref} className="btn-primary">
              {actionLabel}
            </Link>
          ) : (
            <button onClick={onAction} className="btn-primary">
              {actionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default EmptyState;

