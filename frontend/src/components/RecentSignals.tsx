/**
 * Recent Signals Component
 * Displays the 3 most recent change detections with timestamps and source metadata
 */

import React from 'react';
import { Link } from 'react-router-dom';
import type { ChangeItem } from '../services/dashboard';

interface RecentSignalsProps {
  changes: ChangeItem[];
  loading?: boolean;
  error?: string | null;
}

const RecentSignals: React.FC<RecentSignalsProps> = ({ changes, loading, error }) => {
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-3xl font-display font-bold mb-6 tracking-tight">Recent Signals</h2>
        <p className="text-mutedForeground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h2 className="text-3xl font-display font-bold mb-6 tracking-tight">Recent Signals</h2>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (changes.length === 0) {
    return (
      <div className="card">
        <h2 className="text-3xl font-display font-bold mb-6 tracking-tight">Recent Signals</h2>
        <p className="text-mutedForeground">No recent changes detected.</p>
        <div className="mt-4">
          <Link to="/changes" className="btn-secondary inline-block">
            View Full History
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-display font-bold tracking-tight">Recent Signals</h2>
        <Link to="/changes" className="btn-ghost text-sm">
          View Full History →
        </Link>
      </div>
      
      <div className="space-y-4">
        {changes.map((change) => (
          <div
            key={change.id}
            className="border-b-2 border-foreground pb-4 last:border-b-0 last:pb-0"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-4 mb-2">
                  <span className="text-sm font-mono text-mutedForeground">
                    {formatTimestamp(change.detected_at)}
                  </span>
                  {change.is_new && (
                    <span className="text-xs uppercase tracking-widest bg-foreground text-background px-2 py-1">
                      New
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium mb-1">
                  {change.source.name}
                </p>
                <p className="text-sm text-mutedForeground mb-2">
                  {change.route.display}
                </p>
                {change.summary && (
                  <p className="text-sm text-mutedForeground italic">
                    {change.summary}
                  </p>
                )}
              </div>
              <Link
                to={`/changes/${change.id}`}
                className="btn-ghost text-sm ml-4"
              >
                View →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentSignals;

