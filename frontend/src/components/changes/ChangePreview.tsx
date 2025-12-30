/**
 * Change Preview Component
 * Displays a preview of a policy change with truncated diff text
 */

import React from 'react';
import type { PolicyChange } from '../../services/changes';

interface ChangePreviewProps {
  change: PolicyChange;
  onAnalyzeClick?: () => void;
}

/**
 * Truncate text to specified length
 */
const truncateText = (text: string, maxLength: number = 150): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Format timestamp to readable string
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString();
  } catch {
    return timestamp;
  }
};

const ChangePreview: React.FC<ChangePreviewProps> = ({ change, onAnalyzeClick }) => {
  const previewText = truncateText(change.summary || 'Content changed', 150);

  return (
    <div className="border-2 border-foreground bg-background p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Timestamp and Source */}
          <div className="flex items-center gap-4 mb-2">
            <span className="text-xs font-mono text-mutedForeground uppercase tracking-widest">
              {formatTimestamp(change.detected_at)}
            </span>
            <span className="text-sm font-medium text-foreground">
              {change.source.name}
            </span>
            {change.is_new && (
              <span className="inline-flex items-center px-2 py-0.5 text-xs font-semibold bg-green-500 text-white">
                New
              </span>
            )}
          </div>

          {/* Change Preview */}
          <p className="text-sm text-foreground font-body line-clamp-2">
            {previewText}
          </p>
        </div>

        {/* Analyze Diff Button */}
        {onAnalyzeClick && (
          <button
            onClick={onAnalyzeClick}
            className="btn-primary flex-shrink-0"
            aria-label={`Analyze diff for change from ${change.source.name}`}
          >
            Analyze Diff
          </button>
        )}
      </div>
    </div>
  );
};

export default ChangePreview;

