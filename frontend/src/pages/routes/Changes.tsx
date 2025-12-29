/**
 * Route Changes Page Component
 * Displays policy changes for a specific route
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getChangesForRoute } from '../../services/changes';
import type { PolicyChange } from '../../services/changes';
import { getRoutes } from '../../services/routes';
import type { RouteSubscription } from '../../services/routes';
import { generateRouteSummary } from '../../services/ai';
import type { AISummaryResponse } from '../../services/ai';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';
import Pagination from '../../components/Pagination';
import SummaryView from '../../components/ai/SummaryView';

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

const RouteChanges: React.FC = () => {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const [route, setRoute] = useState<RouteSubscription | null>(null);
  const [changes, setChanges] = useState<PolicyChange[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [changesLoading, setChangesLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [changesError, setChangesError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<{
    total: number;
    page: number;
    page_size: number;
  }>({
    total: 0,
    page: 1,
    page_size: 50,
  });
  const [summary, setSummary] = useState<AISummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const currentPage = pagination.page;

  /**
   * Fetch route details
   */
  useEffect(() => {
    if (!routeId) {
      setError('Route ID is required');
      setLoading(false);
      return;
    }

    const fetchRoute = async (): Promise<void> => {
      setLoading(true);
      setError(null);

      try {
        // Fetch all routes and find the one we need
        // Note: In a real app, we'd have GET /api/routes/{id}
        const response = await getRoutes(1, 100);
        const foundRoute = response.items.find((r) => r.id === routeId);

        if (!foundRoute) {
          setError('Route not found');
          setRoute(null);
        } else {
          setRoute(foundRoute);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch route';
        setError(errorMessage);
        setRoute(null);
      } finally {
        setLoading(false);
      }
    };

    fetchRoute();
  }, [routeId]);

  /**
   * Fetch changes for route
   */
  useEffect(() => {
    if (!routeId) {
      return;
    }

    const fetchChanges = async (): Promise<void> => {
      setChangesLoading(true);
      setChangesError(null);

      try {
        const response = await getChangesForRoute(routeId, currentPage, pagination.page_size);
        setChanges(response.items);
        setPagination({
          total: response.total,
          page: response.page,
          page_size: response.page_size,
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch changes';
        setChangesError(errorMessage);
        setChanges([]);
      } finally {
        setChangesLoading(false);
      }
    };

    fetchChanges();
  }, [routeId, currentPage, pagination.page_size]);

  /**
   * Handle page change
   */
  const handlePageChange = (page: number): void => {
    setPagination((prev) => ({ ...prev, page }));
  };

  /**
   * Generate AI summary for route
   */
  const handleGenerateSummary = async (): Promise<void> => {
    if (!routeId) {
      return;
    }

    setSummaryLoading(true);
    setSummaryError(null);
    setSummary(null);

    try {
      const response = await generateRouteSummary(routeId);
      setSummary(response);
    } catch (err) {
      const error = err as Error & { code?: string; status?: number };
      // Handle specific error codes
      if (error.code === 'NOT_IMPLEMENTED' || error.status === 501) {
        setSummaryError('AI summary service is not available. The backend endpoint may not be implemented yet.');
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Failed to generate AI summary';
        setSummaryError(errorMessage);
      }
    } finally {
      setSummaryLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSpinner message="Loading route..." />
        </div>
      </div>
    );
  }

  if (error || !route) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <ErrorMessage
            message={error || 'Route not found'}
            onRetry={() => navigate('/routes')}
            retryLabel="Back to Routes"
          />
        </div>
      </div>
    );
  }

  const totalPages = Math.ceil(pagination.total / pagination.page_size);

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            to={`/routes/${route.id}`}
            className="btn-ghost text-sm mb-2 inline-block"
          >
            ← Back to Route
          </Link>
          <h1 className="text-7xl font-display font-bold tracking-tight">
            Changes for {formatRoute(route.origin_country, route.destination_country)}
          </h1>
          <p className="text-lg font-body text-mutedForeground mt-2">
            {route.visa_type} Visa
          </p>
        </div>

        {/* AI Summary Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-display font-bold uppercase tracking-widest">
              AI Summary
            </h2>
            <div className="flex items-center space-x-2">
              {summary && (
                <button
                  onClick={handleGenerateSummary}
                  disabled={summaryLoading}
                  className="btn-secondary text-xs px-4 py-2"
                >
                  Regenerate
                </button>
              )}
              <button
                onClick={handleGenerateSummary}
                disabled={summaryLoading}
                className="btn-primary text-xs px-4 py-2"
              >
                {summary ? 'Regenerate Summary' : 'Generate AI Summary'}
              </button>
            </div>
          </div>

          {/* Summary Loading */}
          {summaryLoading && (
            <div className="mb-6">
              <LoadingSpinner message="Generating AI summary..." />
            </div>
          )}

          {/* Summary Error */}
          {!summaryLoading && summaryError && (
            <div className="mb-6">
              <ErrorMessage
                message={summaryError}
                onRetry={handleGenerateSummary}
                retryLabel="Try Again"
              />
            </div>
          )}

          {/* Summary Display */}
          {!summaryLoading && !summaryError && summary && (
            <div className="mb-6">
              <SummaryView
                summary={summary.summary}
                generatedAt={summary.generated_at}
              />
            </div>
          )}

          {/* No Summary State */}
          {!summaryLoading && !summaryError && !summary && (
            <div className="border-2 border-foreground bg-background p-6 mb-6">
              <p className="text-sm text-mutedForeground">
                Click "Generate AI Summary" to get an AI-generated explanation of changes for this route.
              </p>
            </div>
          )}
        </div>

        {/* Changes Loading */}
        {changesLoading && <LoadingSpinner message="Loading changes..." />}

        {/* Changes Error */}
        {!changesLoading && changesError && (
          <ErrorMessage
            message={changesError}
            onRetry={() => {
              if (routeId) {
                getChangesForRoute(routeId, currentPage, pagination.page_size)
                  .then((response) => {
                    setChanges(response.items);
                    setPagination({
                      total: response.total,
                      page: response.page,
                      page_size: response.page_size,
                    });
                  })
                  .catch((err) => setChangesError(err.message));
              }
            }}
            retryLabel="Retry"
          />
        )}

        {/* Changes Empty State */}
        {!changesLoading && !changesError && changes.length === 0 && (
          <EmptyState
            title="No changes detected"
            message={`No policy changes have been detected for ${route.destination_country} ${route.visa_type} visa yet.`}
          />
        )}

        {/* Changes List */}
        {!changesLoading && !changesError && changes.length > 0 && (
          <>
            <div className="border-2 border-foreground bg-background overflow-hidden mb-6">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-foreground bg-muted">
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Detected
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Source
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Summary
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Diff Size
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {changes.map((change, index) => (
                    <tr
                      key={change.id}
                      className={`border-b border-borderLight hover:bg-muted transition-colors duration-100 ${
                        index % 2 === 0 ? 'bg-background' : 'bg-muted'
                      }`}
                    >
                      <td className="px-6 py-4 text-sm font-mono text-mutedForeground">
                        {formatDate(change.detected_at)}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        <div>
                          <div className="font-medium">{change.source.name}</div>
                          <a
                            href={change.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-mutedForeground hover:text-foreground underline"
                          >
                            {change.source.url}
                          </a>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {change.summary}
                        {change.is_new && (
                          <span className="ml-2 px-2 py-0.5 bg-foreground text-background text-xs uppercase tracking-widest">
                            New
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-mutedForeground">
                        {change.diff_length} chars
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => navigate(`/changes/${change.id}`)}
                          className="btn-ghost text-xs"
                        >
                          View Diff
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 0 && (
              <Pagination
                currentPage={pagination.page}
                totalPages={totalPages}
                totalItems={pagination.total}
                pageSize={pagination.page_size}
                onPageChange={handlePageChange}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default RouteChanges;

