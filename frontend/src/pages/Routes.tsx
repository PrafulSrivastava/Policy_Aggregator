/**
 * Routes Page Component
 * Displays list of route subscriptions with pagination
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { getRoutes } from '../services/routes';
import type { RouteSubscription, PaginatedRoutesResponse } from '../services/routes';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import Pagination from '../components/Pagination';

/**
 * Format date to YYYY-MM-DD
 */
const formatDate = (dateString: string): string => {
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

const Routes: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [routes, setRoutes] = useState<RouteSubscription[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pagination, setPagination] = useState<{
    total: number;
    page: number;
    page_size: number;
  }>({
    total: 0,
    page: 1,
    page_size: 20,
  });

  // Get page from URL params or default to 1
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('page_size') || '20', 10);

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
   * Fetch routes from API
   */
  const fetchRoutes = async (page: number, size: number): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response: PaginatedRoutesResponse = await getRoutes(page, size);
      setRoutes(response.items);
      setPagination({
        total: response.total,
        page: response.page,
        page_size: response.page_size,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch routes';
      setError(errorMessage);
      setRoutes([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle page change
   */
  const handlePageChange = (page: number): void => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', page.toString());
    setSearchParams(newParams);
  };

  // Fetch routes on mount and when page/pageSize changes
  useEffect(() => {
    fetchRoutes(currentPage, pageSize);
  }, [currentPage, pageSize]);

  // Refresh routes when returning from add page (if success message exists)
  useEffect(() => {
    if (successMessage) {
      fetchRoutes(currentPage, pageSize);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [successMessage]);

  // Calculate total pages
  const totalPages = Math.ceil(pagination.total / pagination.page_size);

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-7xl font-display font-bold tracking-tight">
            Routes
          </h1>
          {!loading && !error && (
            <button
              onClick={() => navigate('/routes/new')}
              className="btn-primary"
            >
              Add Route
            </button>
          )}
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-foreground text-background border-2 border-foreground">
            <p className="text-sm font-medium">{successMessage}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && <LoadingSpinner message="Loading routes..." />}

        {/* Error State */}
        {!loading && error && (
          <ErrorMessage
            message={error}
            onRetry={() => fetchRoutes(currentPage, pageSize)}
            retryLabel="Retry"
          />
        )}

        {/* Empty State */}
        {!loading && !error && routes.length === 0 && (
          <EmptyState
            title="No routes configured yet"
            message="Get started by adding your first route subscription to track policy changes."
            actionLabel="Add Your First Route"
            actionHref="/routes/new"
          />
        )}

        {/* Routes Table */}
        {!loading && !error && routes.length > 0 && (
          <>
            <div className="border-2 border-foreground bg-background overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-foreground bg-muted">
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Route
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Visa Type
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Email
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Created
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {routes.map((route, index) => (
                    <tr
                      key={route.id}
                      className={`border-b border-borderLight hover:bg-muted transition-colors duration-100 ${
                        index % 2 === 0 ? 'bg-background' : 'bg-muted'
                      }`}
                    >
                      <td className="px-6 py-4 text-sm font-body">
                        {formatRoute(route.origin_country, route.destination_country)}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {route.visa_type}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {route.email}
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-mutedForeground">
                        {formatDate(route.created_at)}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        <span
                          className={`uppercase tracking-widest text-xs font-medium ${
                            route.is_active
                              ? 'text-foreground'
                              : 'text-mutedForeground'
                          }`}
                        >
                          {route.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => navigate(`/routes/${route.id}`)}
                            className="btn-ghost text-xs"
                            title="View details and sources"
                          >
                            View
                          </button>
                          <button
                            className="btn-ghost text-xs"
                            disabled
                            title="Edit (coming soon)"
                          >
                            Edit
                          </button>
                          <button
                            className="btn-ghost text-xs"
                            disabled
                            title="Delete (coming soon)"
                          >
                            Delete
                          </button>
                        </div>
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

export default Routes;
