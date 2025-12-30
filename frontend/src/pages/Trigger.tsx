/**
 * Manual Trigger Diagnostics Page
 * Enhanced diagnostics interface for manually triggering source fetches with detailed output
 */

import React, { useState, useEffect } from 'react';
import { getSources, triggerSourceFetch, type Source, type TriggerSourceResponse } from '../services/sources';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Select from '../components/forms/Select';
import TerminalOutput from '../components/diagnostics/TerminalOutput';
import ResultVisualization from '../components/diagnostics/ResultVisualization';

const Trigger: React.FC = () => {
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [fetching, setFetching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [fetchResult, setFetchResult] = useState<TriggerSourceResponse | null>(null);
  const [fetchStartTime, setFetchStartTime] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  /**
   * Fetch all sources for dropdown
   */
  useEffect(() => {
    const fetchSourcesList = async (): Promise<void> => {
      setLoading(true);
      setError(null);

      try {
        const response = await getSources(1, 100); // Get up to 100 sources
        setSources(response.items);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch sources';
        setError(errorMessage);
        setSources([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSourcesList();
  }, []);

  /**
   * Add log message to terminal output
   */
  const addTerminalLog = (message: string): void => {
    setTerminalLogs((prev) => [...prev, message]);
  };

  /**
   * Clear terminal output
   */
  const clearTerminal = (): void => {
    setTerminalLogs([]);
    setFetchResult(null);
    setLatency(null);
  };

  /**
   * Simulate network handshake messages
   */
  const simulateNetworkHandshake = (): void => {
    addTerminalLog('[NETWORK] Establishing connection...');
    setTimeout(() => {
      addTerminalLog('[NETWORK] TCP handshake completed');
    }, 200);
    setTimeout(() => {
      addTerminalLog('[NETWORK] SSL/TLS negotiation successful');
    }, 400);
  };

  /**
   * Simulate packet resolution messages
   */
  const simulatePacketResolution = (): void => {
    setTimeout(() => {
      addTerminalLog('[PACKET] Resolving DNS...');
    }, 600);
    setTimeout(() => {
      addTerminalLog('[PACKET] DNS resolved: 192.168.1.1');
    }, 800);
    setTimeout(() => {
      addTerminalLog('[PACKET] Route established');
    }, 1000);
  };

  /**
   * Handle fetch trigger
   */
  const handleTriggerFetch = async (): Promise<void> => {
    if (!selectedSourceId) {
      setError('Please select a source');
      return;
    }

    // Reset state
    clearTerminal();
    setFetching(true);
    setError(null);
    setFetchResult(null);
    setFetchStartTime(Date.now());

    // Add initial log
    addTerminalLog('[SYSTEM] Initializing fetch operation...');
    addTerminalLog(`[SYSTEM] Target Node: ${sources.find(s => s.id === selectedSourceId)?.name || selectedSourceId}`);

    // Simulate network operations
    simulateNetworkHandshake();
    simulatePacketResolution();

    try {
      // Add fetch start log
      setTimeout(() => {
        addTerminalLog('[FETCH] Starting content retrieval...');
      }, 1200);

      // Call API
      const result = await triggerSourceFetch(selectedSourceId);

      // Calculate latency
      const endTime = Date.now();
      const startTime = fetchStartTime || Date.now();
      const calculatedLatency = endTime - startTime;
      setLatency(calculatedLatency);
      setFetchResult(result);

      // Add success logs
      addTerminalLog('[FETCH] Content retrieved successfully');
      addTerminalLog(`[FETCH] Change detected: ${result.changeDetected ? 'Yes' : 'No'}`);
      if (result.policyVersionId) {
        addTerminalLog(`[FETCH] Policy Version ID: ${result.policyVersionId}`);
      }
      if (result.policyChangeId) {
        addTerminalLog(`[FETCH] Policy Change ID: ${result.policyChangeId}`);
      }
      addTerminalLog('[SYSTEM] Fetch operation completed');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger fetch';
      setError(errorMessage);
      addTerminalLog(`[ERROR] ${errorMessage}`);
      addTerminalLog('[SYSTEM] Fetch operation failed');
    } finally {
      setFetching(false);
    }
  };

  /**
   * Prepare source options for dropdown
   */
  const sourceOptions = sources.map((source) => ({
    value: source.id,
    label: `${source.name} (${source.country} - ${source.visa_type})`,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold mb-2">Manual Trigger Diagnostics</h1>
        <p className="text-mutedForeground">
          Test source configurations and debug issues with detailed fetch diagnostics
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <ErrorMessage
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {/* Execution Control Section */}
      <div className="card space-y-4">
        <h2 className="text-xl font-display font-semibold uppercase tracking-widest">
          Execution Control
        </h2>
        
        {loading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-4">
            <Select
              id="source-select"
              label="Target Node (Source)"
              options={sourceOptions}
              value={selectedSourceId}
              onChange={(e) => setSelectedSourceId(e.target.value)}
              placeholder="Select a source..."
              required
              disabled={fetching}
            />

            <div className="flex gap-4">
              <button
                type="button"
                onClick={handleTriggerFetch}
                disabled={!selectedSourceId || fetching}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {fetching ? 'Fetching...' : 'Initialize Fetch'}
              </button>
              
              {terminalLogs.length > 0 && (
                <button
                  type="button"
                  onClick={clearTerminal}
                  disabled={fetching}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Clear Terminal
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Terminal Output Section */}
      <TerminalOutput logs={terminalLogs} />

      {/* Result Visualization Section */}
      {fetchResult && (
        <ResultVisualization
          result={fetchResult}
          latency={latency}
        />
      )}
    </div>
  );
};

export default Trigger;

