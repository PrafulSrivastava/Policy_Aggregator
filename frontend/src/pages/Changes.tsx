/**
 * Changes Page Component
 * Displays chronological feed of policy changes with navigation to details
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getChanges, type PolicyChange, type PaginatedChangesResponse } from '../services/changes';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import Pagination from '../components/Pagination';
import ChangePreview from '../components/changes/ChangePreview';

const Changes: React.FC = () => {
  const navigate = useNavigate();
  const [changes, setChanges] = useState<PolicyChange[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [pageSize] = useState<number>(50);

  /**
   * Fetch changes from API
   */
  const fetchChanges = async (page: number = 1): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response: PaginatedChangesResponse = await getChanges(page, pageSize);
      setChanges(response.items);
      setTotalItems(response.total);
      setTotalPages(response.pages || Math.ceil(response.total / pageSize));
      setCurrentPage(response.page);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch changes';
      setError(errorMessage);
      setChanges([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChanges(currentPage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  /**
   * Handle page change
   */
  const handlePageChange = (page: number): void => {
    setCurrentPage(page);
    // Scroll to top when page changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  /**
   * Handle retry after error
   */
  const handleRetry = (): void => {
    fetchChanges(currentPage);
  };

  /**
   * Handle Analyze Diff button click
   */
  const handleAnalyzeDiff = (changeId: string): void => {
    navigate(`/changes/${changeId}`);
  };

  if (loading && changes.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  if (error && changes.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <ErrorMessage
            message={error}
            onRetry={handleRetry}
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
          <h1 className="text-7xl font-display font-bold mb-4 tracking-tight">
            Change History
          </h1>
          <p className="text-xl font-body text-mutedForeground">
            Chronological feed of detected policy variances
          </p>
        </div>

        {/* Changes List */}
        {changes.length === 0 ? (
          <EmptyState
            title="No changes found"
            message="No policy changes have been detected yet."
          />
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {changes.map((change) => (
                <ChangePreview
                  key={change.id}
                  change={change}
                  onAnalyzeClick={() => handleAnalyzeDiff(change.id)}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={totalItems}
                pageSize={pageSize}
                onPageChange={handlePageChange}
                itemLabel="changes"
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Changes;
