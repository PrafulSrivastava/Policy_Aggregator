/**
 * Route Detail Page Component
 * Displays route details and associated sources
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { getSourcesForRoute } from '../../services/sources';
import type { Source } from '../../services/sources';
import { getRoutes } from '../../services/routes';
import type { RouteSubscription } from '../../services/routes';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import EmptyState from '../../components/EmptyState';

/**
 * Format date to YYYY-MM-DD
 */
const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  try {
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
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

const RouteDetail: React.FC = () => {
  const { routeId } = useParams<{ routeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [route, setRoute] = useState<RouteSubscription | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [sourcesLoading, setSourcesLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sourcesError, setSourcesError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Check for success message from navigation state
  useEffect(() => {
    if (location.state && typeof location.state === 'object' && 'message' in location.state) {
      setSuccessMessage(location.state.message as string);
      // Clear the state to prevent showing message on refresh
      window.history.replaceState({}, document.title);
      // Auto-hide success message after 5 seconds
      const timer = setTimeout(() => {
        setSuccessMessage(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [location.state]);

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
   * Fetch sources for route
   */
  useEffect(() => {
    if (!route) {
      return;
    }

    const fetchSources = async (): Promise<void> => {
      setSourcesLoading(true);
      setSourcesError(null);

      try {
        const response = await getSourcesForRoute(
          route.destination_country,
          route.visa_type,
          1,
          100
        );
        setSources(response.items);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch sources';
        setSourcesError(errorMessage);
        setSources([]);
      } finally {
        setSourcesLoading(false);
      }
    };

    fetchSources();
  }, [route]);

  // Refresh sources when success message appears (source was just added)
  useEffect(() => {
    if (successMessage && route) {
      const fetchSources = async (): Promise<void> => {
        try {
          const response = await getSourcesForRoute(
            route.destination_country,
            route.visa_type,
            1,
            100
          );
          setSources(response.items);
        } catch (err) {
          // Silently fail refresh
          console.error('Failed to refresh sources:', err);
        }
      };
      fetchSources();
    }
  }, [successMessage, route]);

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

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link
              to="/routes"
              className="btn-ghost text-sm mb-2 inline-block"
            >
              ← Back to Routes
            </Link>
            <h1 className="text-7xl font-display font-bold tracking-tight">
              {formatRoute(route.origin_country, route.destination_country)}
            </h1>
            <p className="text-lg font-body text-mutedForeground mt-2">
              {route.visa_type} Visa
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(`/routes/${route.id}/changes`)}
              className="btn-secondary"
            >
              View Changes
            </button>
            <button
              onClick={() => navigate('/sources/new', { state: { route } })}
              className="btn-primary"
            >
              Add Source
            </button>
          </div>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-foreground text-background border-2 border-foreground">
            <p className="text-sm font-medium">{successMessage}</p>
          </div>
        )}

        {/* Route Details */}
        <div className="card mb-8">
          <h2 className="text-3xl font-display font-bold mb-4 tracking-tight">
            Route Details
          </h2>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Origin Country
              </dt>
              <dd className="text-lg font-body">{route.origin_country}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Destination Country
              </dt>
              <dd className="text-lg font-body">{route.destination_country}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Visa Type
              </dt>
              <dd className="text-lg font-body">{route.visa_type}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Email
              </dt>
              <dd className="text-lg font-body">{route.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Status
              </dt>
              <dd className="text-lg font-body">
                <span
                  className={`uppercase tracking-widest text-xs font-medium ${
                    route.is_active
                      ? 'text-foreground'
                      : 'text-mutedForeground'
                  }`}
                >
                  {route.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium uppercase tracking-widest text-mutedForeground mb-1">
                Created
              </dt>
              <dd className="text-lg font-mono text-mutedForeground">
                {formatDate(route.created_at)}
              </dd>
            </div>
          </dl>
        </div>

        {/* Sources Section */}
        <div>
          <h2 className="text-5xl font-display font-bold mb-6 tracking-tight">
            Sources
          </h2>

          {/* Sources Loading */}
          {sourcesLoading && <LoadingSpinner message="Loading sources..." />}

          {/* Sources Error */}
          {!sourcesLoading && sourcesError && (
            <ErrorMessage
              message={sourcesError}
              onRetry={() => {
                // Re-fetch sources
                if (route) {
                  getSourcesForRoute(route.destination_country, route.visa_type, 1, 100)
                    .then((response) => setSources(response.items))
                    .catch((err) => setSourcesError(err.message));
                }
              }}
              retryLabel="Retry"
            />
          )}

          {/* Sources Empty State */}
          {!sourcesLoading && !sourcesError && sources.length === 0 && (
            <EmptyState
              title="No sources configured"
              message={`No sources have been added for ${route.destination_country} ${route.visa_type} visa yet.`}
              actionLabel="Add First Source"
              onAction={() => navigate('/sources/new', { state: { route } })}
            />
          )}

          {/* Sources List */}
          {!sourcesLoading && !sourcesError && sources.length > 0 && (
            <div className="border-2 border-foreground bg-background overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-foreground bg-muted">
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Name
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      URL
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Fetch Type
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Frequency
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Last Checked
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source, index) => (
                    <tr
                      key={source.id}
                      className={`border-b border-borderLight hover:bg-muted transition-colors duration-100 ${
                        index % 2 === 0 ? 'bg-background' : 'bg-muted'
                      }`}
                    >
                      <td className="px-6 py-4 text-sm font-body">
                        {source.name}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-foreground underline hover:text-mutedForeground"
                        >
                          {source.url}
                        </a>
                      </td>
                      <td className="px-6 py-4 text-sm font-body uppercase">
                        {source.fetch_type}
                      </td>
                      <td className="px-6 py-4 text-sm font-body capitalize">
                        {source.check_frequency}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        <span
                          className={`uppercase tracking-widest text-xs font-medium ${
                            source.is_active
                              ? 'text-foreground'
                              : 'text-mutedForeground'
                          }`}
                        >
                          {source.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-mutedForeground">
                        {formatDate(source.last_checked_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RouteDetail;

