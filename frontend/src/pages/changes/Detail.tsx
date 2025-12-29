/**
 * Change Detail Page Component
 * Displays detailed information for a specific policy change including full diff
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getChangeDetail } from '../../services/changes';
import type { PolicyChangeDetail } from '../../services/changes';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import DiffView from '../../components/changes/DiffView';

/**
 * Format date to readable format
 */
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

/**
 * Format route display: Origin → Destination
 */
const formatRoute = (origin: string, destination: string): string => {
  return `${origin} → ${destination}`;
};

const ChangeDetail: React.FC = () => {
  const { changeId } = useParams<{ changeId: string }>();
  const navigate = useNavigate();
  const [change, setChange] = useState<PolicyChangeDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch change detail
   */
  useEffect(() => {
    if (!changeId) {
      setError('Change ID is required');
      setLoading(false);
      return;
    }

    const fetchChange = async (): Promise<void> => {
      setLoading(true);
      setError(null);

      try {
        const changeDetail = await getChangeDetail(changeId);
        setChange(changeDetail);
      } catch (err) {
        if (err instanceof Error) {
          const errorWithCode = err as Error & { code?: string };
          if (errorWithCode.code === 'CHANGE_NOT_FOUND') {
            setError('Change not found');
          } else {
            setError(err.message || 'Failed to fetch change');
          }
        } else {
          setError('Failed to fetch change');
        }
        setChange(null);
      } finally {
        setLoading(false);
      }
    };

    fetchChange();
  }, [changeId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSpinner message="Loading change..." />
        </div>
      </div>
    );
  }

  if (error || !change) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <ErrorMessage
            message={error || 'Change not found'}
            onRetry={() => navigate('/changes')}
            retryLabel="Back to Changes"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            {change.route && (
              <Link
                to={`/routes/${change.route.id}/changes`}
                className="btn-ghost text-sm"
              >
                ← Back to Route Changes
              </Link>
            )}
            <Link
              to="/changes"
              className="btn-ghost text-sm"
            >
              All Changes
            </Link>
          </div>
          <h1 className="text-7xl font-display font-bold tracking-tight">
            Policy Change
          </h1>
          <p className="text-lg font-body text-mutedForeground mt-2">
            Detected {formatDate(change.detected_at)}
          </p>
        </div>

        {/* Change Information */}
        <div className="card mb-8">
          <h2 className="text-3xl font-display font-bold mb-4 tracking-tight">
            Change Information
          </h2>
          <dl className="grid grid-cols-2 gap-4">
            {change.route && (
              <>
                <div>
                  <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                    Route
                  </dt>
                  <dd className="text-lg font-body">
                    {formatRoute(change.route.origin_country, change.route.destination_country)} ({change.route.visa_type})
                  </dd>
                </div>
              </>
            )}
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Source
              </dt>
              <dd className="text-lg font-body">
                <div>
                  <div className="font-medium">{change.source.name}</div>
                  <a
                    href={change.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-mutedForeground hover:text-foreground underline"
                  >
                    {change.source.url}
                  </a>
                </div>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Detected At
              </dt>
              <dd className="text-lg font-mono text-mutedForeground">
                {formatDate(change.detected_at)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Summary
              </dt>
              <dd className="text-lg font-body">
                {change.summary}
                {change.is_new && (
                  <span className="ml-2 px-2 py-0.5 bg-foreground text-background text-xs uppercase tracking-widest">
                    New
                  </span>
                )}
              </dd>
            </div>
            {change.old_version && (
              <div>
                <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                  Old Version
                </dt>
                <dd className="text-lg font-mono text-mutedForeground">
                  {formatDate(change.old_version.fetched_at)} ({change.old_version.content_length} chars)
                </dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                New Version
              </dt>
              <dd className="text-lg font-mono text-mutedForeground">
                {formatDate(change.new_version.fetched_at)} ({change.new_version.content_length} chars)
              </dd>
            </div>
          </dl>
        </div>

        {/* Navigation */}
        {(change.previous_change_id || change.next_change_id) && (
          <div className="flex items-center justify-between mb-8">
            {change.previous_change_id ? (
              <button
                onClick={() => navigate(`/changes/${change.previous_change_id}`)}
                className="btn-secondary"
              >
                ← Previous Change
              </button>
            ) : (
              <div></div>
            )}
            {change.next_change_id ? (
              <button
                onClick={() => navigate(`/changes/${change.next_change_id}`)}
                className="btn-secondary"
              >
                Next Change →
              </button>
            ) : (
              <div></div>
            )}
          </div>
        )}

        {/* Diff Display */}
        <div>
          <h2 className="text-5xl font-display font-bold mb-6 tracking-tight">
            Diff
          </h2>
          <DiffView diff={change.diff} className="max-h-[600px]" />
        </div>
      </div>
    </div>
  );
};

export default ChangeDetail;

