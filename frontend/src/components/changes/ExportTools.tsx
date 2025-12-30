/**
 * Export Tools Component
 * Provides export functionality for policy changes
 */

import React from 'react';
import type { PolicyChangeDetail } from '../../services/changes';

interface ExportToolsProps {
  change: PolicyChangeDetail;
  className?: string;
}

/**
 * Export change data as JSON
 */
const exportAsJSON = (change: PolicyChangeDetail): void => {
  const exportData = {
    id: change.id,
    detected_at: change.detected_at,
    summary: change.summary,
    is_new: change.is_new,
    diff_length: change.diff_length,
    source: {
      id: change.source.id,
      name: change.source.name,
      url: change.source.url,
      country: change.source.country,
      visa_type: change.source.visa_type,
    },
    route: change.route ? {
      id: change.route.id,
      origin_country: change.route.origin_country,
      destination_country: change.route.destination_country,
      visa_type: change.route.visa_type,
      display: change.route.display,
    } : null,
    diff: change.diff,
    old_version: change.old_version ? {
      id: change.old_version.id,
      content_hash: change.old_version.content_hash,
      fetched_at: change.old_version.fetched_at,
      content_length: change.old_version.content_length,
    } : null,
    new_version: {
      id: change.new_version.id,
      content_hash: change.new_version.content_hash,
      fetched_at: change.new_version.fetched_at,
      content_length: change.new_version.content_length,
    },
    exported_at: new Date().toISOString(),
  };

  const jsonString = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `policy-change-${change.id}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

const ExportTools: React.FC<ExportToolsProps> = ({ change, className = '' }) => {
  const handleSourceLink = (): void => {
    if (change.source.url) {
      window.open(change.source.url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleExportJSON = (): void => {
    exportAsJSON(change);
  };

  return (
    <div className={`border-2 border-foreground bg-background ${className}`}>
      <div className="p-6">
        <h3 className="text-3xl font-display font-bold mb-4 tracking-tight">
          Export Tools
        </h3>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={handleSourceLink}
            className="btn-primary"
            disabled={!change.source.url}
            aria-label="Open source URL in new tab"
          >
            Source Link
          </button>
          <button
            onClick={handleExportJSON}
            className="btn-secondary"
            aria-label="Export change data as JSON"
          >
            Export JSON
          </button>
        </div>
        {!change.source.url && (
          <p className="text-xs text-mutedForeground mt-2">
            Source URL is not available for this change.
          </p>
        )}
      </div>
    </div>
  );
};

export default ExportTools;

