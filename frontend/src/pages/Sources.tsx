/**
 * Sources Page Component
 * Displays sources list with status indicators and management actions
 */

import React, { useState, useEffect } from 'react';
import { getSystemStatus, triggerSourceFetch, type Source, type TriggerSourceResponse } from '../services/sources';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import StatusBadge, { type SourceStatus } from '../components/sources/StatusBadge';
import SourceModal from '../components/sources/SourceModal';

/**
 * Truncate URL for display
 */
const truncateUrl = (url: string, maxLength: number = 50): string => {
  if (url.length <= maxLength) {
    return url;
  }
  return `${url.substring(0, maxLength)}...`;
};


const Sources: React.FC = () => {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [triggeringSourceId, setTriggeringSourceId] = useState<string | null>(null);
  const [triggerResult, setTriggerResult] = useState<{ sourceId: string; success: boolean; message: string } | null>(null);

  /**
   * Fetch sources with status
   */
  const fetchSources = async (): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const statusData = await getSystemStatus();
      setSources(statusData.sources);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch sources';
      setError(errorMessage);
      setSources([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
    
    // Refresh sources every 30 seconds
    const interval = setInterval(fetchSources, 30000);
    return () => clearInterval(interval);
  }, []);

  /**
   * Handle modal close
   */
  const handleModalClose = (): void => {
    setIsModalOpen(false);
    setEditingSource(null);
  };

  /**
   * Handle modal success (after create/update)
   */
  const handleModalSuccess = (): void => {
    fetchSources();
  };

  /**
   * Handle "Add Node" button click
   */
  const handleAddNode = (): void => {
    setEditingSource(null);
    setIsModalOpen(true);
  };

  /**
   * Handle "Edit" button click
   */
  const handleEdit = (source: Source): void => {
    setEditingSource(source);
    setIsModalOpen(true);
  };

  /**
   * Handle "Play" button click (trigger fetch)
   */
  const handlePlay = async (source: Source): Promise<void> => {
    setTriggeringSourceId(source.id);
    setTriggerResult(null);

    try {
      const result: TriggerSourceResponse = await triggerSourceFetch(source.id);
      
      setTriggerResult({
        sourceId: source.id,
        success: result.success,
        message: result.success
          ? `Fetch completed${result.changeDetected ? ' - Change detected!' : ' - No changes'}`
          : `Fetch failed: ${result.error || 'Unknown error'}`,
      });

      // Refresh sources after trigger to update status
      await fetchSources();

      // Clear result after 5 seconds
      setTimeout(() => {
        setTriggerResult(null);
      }, 5000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger fetch';
      setTriggerResult({
        sourceId: source.id,
        success: false,
        message: errorMessage,
      });

      // Clear result after 5 seconds
      setTimeout(() => {
        setTriggerResult(null);
      }, 5000);
    } finally {
      setTriggeringSourceId(null);
    }
  };

  if (loading && sources.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  if (error && sources.length === 0) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <ErrorMessage message={error} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-7xl font-display font-bold tracking-tight">
            Sources
          </h1>
          <button
            onClick={handleAddNode}
            className="btn-primary"
            aria-label="Add new source"
          >
            Add Node
          </button>
        </div>

        {/* Sources Table */}
        {sources.length === 0 ? (
          <EmptyState
            title="No sources found"
            message="Get started by adding your first source."
            actionLabel="Add Node"
            onAction={handleAddNode}
          />
        ) : (
          <div className="bg-background border-2 border-foreground overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-foreground">
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Name</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Target URL</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Region</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Visa Type</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Fetch Method</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Frequency</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Health Status</th>
                  <th className="px-6 py-4 text-left text-sm font-medium uppercase tracking-widest">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-foreground">
                {sources.map((source) => {
                  const isTriggering = triggeringSourceId === source.id;
                  const result = triggerResult?.sourceId === source.id ? triggerResult : null;
                  const status: SourceStatus = source.status || 'never_checked';

                  return (
                    <tr key={source.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {source.name}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-900 underline"
                          title={source.url}
                        >
                          {truncateUrl(source.url)}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {source.country}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {source.visa_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold bg-gray-200 text-gray-800 uppercase">
                          {source.fetch_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2 py-1 text-xs font-semibold bg-gray-200 text-gray-800 capitalize">
                          {source.check_frequency}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handlePlay(source)}
                            disabled={isTriggering}
                            className="btn-secondary text-sm px-3 py-1"
                            aria-label={`Trigger fetch for ${source.name}`}
                            title="Trigger fetch"
                          >
                            {isTriggering ? '...' : '▶'}
                          </button>
                          <button
                            onClick={() => handleEdit(source)}
                            className="btn-secondary text-sm px-3 py-1"
                            aria-label={`Edit ${source.name}`}
                            title="Edit source"
                          >
                            Edit
                          </button>
                        </div>
                        {result && (
                          <div className={`mt-2 text-xs ${result.success ? 'text-green-600' : 'text-red-600'}`}>
                            {result.message}
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Source Modal */}
        <SourceModal
          isOpen={isModalOpen}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
          source={editingSource}
        />
      </div>
    </div>
  );
};

export default Sources;
