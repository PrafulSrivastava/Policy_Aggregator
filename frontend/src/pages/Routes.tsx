/**
 * Routes Page Component
 * Displays list of route subscriptions with pagination
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { getRoutes } from '../services/routes';
import type { RouteSubscription, PaginatedRoutesResponse } from '../services/routes';
import { getChanges } from '../services/changes';
import { getSources } from '../services/sources';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import Pagination from '../components/Pagination';
import RouteModal from '../components/routes/RouteModal';

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


interface RouteMetadata {
  sourceCount: number;
  varianceStatus: string;
}

const Routes: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [routes, setRoutes] = useState<RouteSubscription[]>([]);
  const [routeMetadata, setRouteMetadata] = useState<Record<string, RouteMetadata>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRoute, setEditingRoute] = useState<RouteSubscription | null>(null);
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
   * Fetch metadata for routes (source count and variance status)
   */
  const fetchRouteMetadata = async (routesList: RouteSubscription[]): Promise<void> => {
    const metadata: Record<string, RouteMetadata> = {};

    // Fetch metadata for each route
    await Promise.all(
      routesList.map(async (route) => {
        try {
          // Fetch sources for this route (matching destination country and visa type)
          const sourcesResponse = await getSources(1, 100, {
            country: route.destination_country,
            visa_type: route.visa_type,
          });
          const sourceCount = sourcesResponse?.total || 0;

          // Fetch recent changes for this route (last 7 days)
          const sevenDaysAgo = new Date();
          sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
          const changesResponse = await getChanges(1, 1, {
            route_id: route.id,
            start_date: sevenDaysAgo.toISOString().split('T')[0],
          });
          const recentChangesCount = changesResponse?.total || 0;
          const varianceStatus = recentChangesCount > 0 ? 'Active' : 'Stable';

          metadata[route.id] = {
            sourceCount,
            varianceStatus,
          };
        } catch {
          // If metadata fetch fails, use defaults
          metadata[route.id] = {
            sourceCount: 0,
            varianceStatus: 'Unknown',
          };
        }
      })
    );

    setRouteMetadata(metadata);
  };

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

      // Fetch metadata for routes
      await fetchRouteMetadata(response.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch routes';
      setError(errorMessage);
      setRoutes([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle modal open for create
   */
  const handleCreateRoute = (): void => {
    setEditingRoute(null);
    setModalOpen(true);
  };

  /**
   * Handle modal open for edit
   */
  const handleEditRoute = (route: RouteSubscription): void => {
    setEditingRoute(route);
    setModalOpen(true);
  };

  /**
   * Handle modal close
   */
  const handleCloseModal = (): void => {
    setModalOpen(false);
    setEditingRoute(null);
  };

  /**
   * Handle successful route save
   */
  const handleRouteSaved = (): void => {
    fetchRoutes(currentPage, pageSize);
    setSuccessMessage(
      editingRoute
        ? 'Route updated successfully'
        : 'Route created successfully'
    );
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
              onClick={handleCreateRoute}
              className="btn-primary"
            >
              Initialize Route
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
                      Origin Country
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Destination Country
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Visa Classification
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Created Date
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Variance Status
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-display font-bold uppercase tracking-widest">
                      Associated Source Count
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
                        {route.origin_country}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {route.destination_country}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {route.visa_type}
                      </td>
                      <td className="px-6 py-4 text-sm font-mono text-mutedForeground">
                        {formatDate(route.created_at)}
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        <span
                          className={`uppercase tracking-widest text-xs font-medium ${
                            routeMetadata[route.id]?.varianceStatus === 'Active'
                              ? 'text-foreground'
                              : 'text-mutedForeground'
                          }`}
                        >
                          {routeMetadata[route.id]?.varianceStatus || 'Loading...'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm font-body">
                        {routeMetadata[route.id]?.sourceCount ?? '...'}
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
                            onClick={() => handleEditRoute(route)}
                            className="btn-ghost text-xs"
                            title="Edit route"
                          >
                            Edit
                          </button>
                          <button
                            className="btn-ghost text-xs"
                            title="Delete route (visual trigger)"
                            disabled
                          >
                            Del
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

        {/* Route Modal */}
        <RouteModal
          isOpen={modalOpen}
          onClose={handleCloseModal}
          onSuccess={handleRouteSaved}
          route={editingRoute}
        />
      </div>
    </div>
  );
};

export default Routes;
