/**
 * Result Visualization Component
 * Displays fetch results: latency, variance detection, content hash
 */

import React from 'react';
import { type TriggerSourceResponse } from '../../services/sources';

interface ResultVisualizationProps {
  result: TriggerSourceResponse;
  latency: number | null;
}

const ResultVisualization: React.FC<ResultVisualizationProps> = ({ result, latency }) => {
  /**
   * Format latency duration
   */
  const formatLatency = (ms: number | null): string => {
    if (ms === null) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  /**
   * Get content hash from policy version
   * Note: API doesn't return contentHash directly, would need to fetch from policy version
   * For now, we'll show the policy version ID as a reference
   */
  const getContentHashDisplay = (): string => {
    if (result.policyVersionId) {
      // In a real implementation, we'd fetch the policy version to get contentHash
      // For now, show a truncated version ID as placeholder
      return `${result.policyVersionId.substring(0, 16)}...`;
    }
    return 'N/A';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-display font-semibold uppercase tracking-widest mb-4">
        Result Visualization
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Latency Duration */}
        <div>
          <div className="text-sm uppercase tracking-widest text-mutedForeground mb-2">
            Latency Duration
          </div>
          <div className="text-2xl font-mono font-semibold">
            {formatLatency(latency)}
          </div>
        </div>

        {/* Variance Detection Status */}
        <div>
          <div className="text-sm uppercase tracking-widest text-mutedForeground mb-2">
            Variance Detection
          </div>
          <div className="text-2xl font-semibold">
            {result.changeDetected ? (
              <span className="text-green-600">Yes</span>
            ) : (
              <span className="text-gray-500">No</span>
            )}
          </div>
        </div>

        {/* Content Hash Signature */}
        <div>
          <div className="text-sm uppercase tracking-widest text-mutedForeground mb-2">
            Content Hash Signature
          </div>
          <div className="text-sm font-mono break-all">
            {getContentHashDisplay()}
          </div>
        </div>
      </div>

      {/* Additional Details */}
      <div className="mt-6 pt-6 border-t border-black space-y-2">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-mutedForeground uppercase tracking-widest">Status:</span>
            <span className="ml-2 font-semibold">
              {result.success ? 'Success' : 'Failed'}
            </span>
          </div>
          {result.fetchedAt && (
            <div>
              <span className="text-mutedForeground uppercase tracking-widest">Fetched At:</span>
              <span className="ml-2 font-mono">
                {new Date(result.fetchedAt).toLocaleString()}
              </span>
            </div>
          )}
          {result.policyVersionId && (
            <div>
              <span className="text-mutedForeground uppercase tracking-widest">Version ID:</span>
              <span className="ml-2 font-mono text-xs break-all">
                {result.policyVersionId}
              </span>
            </div>
          )}
          {result.policyChangeId && (
            <div>
              <span className="text-mutedForeground uppercase tracking-widest">Change ID:</span>
              <span className="ml-2 font-mono text-xs break-all">
                {result.policyChangeId}
              </span>
            </div>
          )}
        </div>

        {result.error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-500">
            <div className="text-sm font-semibold text-red-700 uppercase tracking-widest mb-1">
              Error
            </div>
            <div className="text-sm text-red-600">{result.error}</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultVisualization;

