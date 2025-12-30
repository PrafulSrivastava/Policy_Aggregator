/**
 * AI Intelligence Component
 * Displays AI-generated synthesis and impact assessment for policy changes
 */

import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../LoadingSpinner';
import SummaryView from '../ai/SummaryView';
import type { PolicyChangeDetail } from '../../services/changes';
import { generateRouteSummary } from '../../services/ai';
import type { AISummaryResponse } from '../../services/ai';

interface AIIntelligenceProps {
  change: PolicyChangeDetail;
  className?: string;
}

/**
 * Calculate impact assessment based on change characteristics
 * This is a placeholder until backend provides impact assessment
 */
const calculateImpactAssessment = (change: PolicyChangeDetail): {
  severity: 'Low' | 'Medium' | 'High';
  explanation: string;
} => {
  const diffLength = change.diff_length || 0;
  const hasLargeDiff = diffLength > 500;
  const hasRoute = !!change.route;

  if (hasLargeDiff && hasRoute) {
    return {
      severity: 'High',
      explanation: 'Significant content changes detected. This may affect visa requirements or application processes.',
    };
  } else if (diffLength > 200) {
    return {
      severity: 'Medium',
      explanation: 'Moderate content changes detected. Review recommended to understand implications.',
    };
  } else {
    return {
      severity: 'Low',
      explanation: 'Minor content changes detected. Likely updates to formatting or minor clarifications.',
    };
  }
};

const AIIntelligence: React.FC<AIIntelligenceProps> = ({ change, className = '' }) => {
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState<boolean>(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [summaryGeneratedAt, setSummaryGeneratedAt] = useState<string | null>(null);

  const impactAssessment = calculateImpactAssessment(change);

  /**
   * Generate AI summary if route is available
   */
  useEffect(() => {
    if (!change.route?.id) {
      return;
    }

    const fetchSummary = async (): Promise<void> => {
      setSummaryLoading(true);
      setSummaryError(null);

      try {
        const response: AISummaryResponse = await generateRouteSummary(change.route!.id);
        setAiSummary(response.summary);
        setSummaryGeneratedAt(response.generated_at);
      } catch (err) {
        // Handle gracefully - AI service may not be available
        if (err instanceof Error) {
          const errorWithCode = err as Error & { code?: string; status?: number };
          if (errorWithCode.code === 'NOT_IMPLEMENTED' || errorWithCode.status === 501) {
            // AI service not available - this is okay, just don't show summary
            setSummaryError(null);
          } else {
            setSummaryError(err.message || 'Failed to generate AI summary');
          }
        } else {
          setSummaryError('Failed to generate AI summary');
        }
      } finally {
        setSummaryLoading(false);
      }
    };

    fetchSummary();
  }, [change.route?.id]);

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'High':
        return 'bg-red-500 text-white';
      case 'Medium':
        return 'bg-yellow-500 text-black';
      case 'Low':
        return 'bg-green-500 text-white';
      default:
        return 'bg-gray-400 text-white';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* AI Synthesis Section */}
      <div className="border-2 border-foreground bg-background">
        <div className="p-6">
          <h3 className="text-3xl font-display font-bold mb-4 tracking-tight">
            AI Intelligence
          </h3>

          {summaryLoading && (
            <div className="py-8">
              <LoadingSpinner message="Generating AI summary..." />
            </div>
          )}

          {summaryError && !summaryLoading && (
            <div className="p-4 bg-foreground text-background border-2 border-foreground">
              <p className="text-sm font-medium">{summaryError}</p>
              <p className="text-xs mt-2 opacity-90">
                AI summary generation is not available. Please review the diff below for details.
              </p>
            </div>
          )}

          {aiSummary && !summaryLoading && !summaryError && (
            <div className="mb-6">
              <h4 className="text-sm font-display font-bold mb-3 uppercase tracking-widest">
                Synthesis
              </h4>
              <SummaryView
                summary={aiSummary}
                generatedAt={summaryGeneratedAt || undefined}
              />
            </div>
          )}

          {!aiSummary && !summaryLoading && !summaryError && change.route && (
            <div className="p-4 bg-gray-100 text-gray-700 border-2 border-gray-300">
              <p className="text-sm">
                AI summary generation is not available for this change. Please review the diff below for details.
              </p>
            </div>
          )}

          {!change.route && (
            <div className="p-4 bg-gray-100 text-gray-700 border-2 border-gray-300">
              <p className="text-sm">
                AI summary is not available for changes without an associated route.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Impact Assessment Section */}
      <div className="border-2 border-foreground bg-background">
        <div className="p-6">
          <h4 className="text-sm font-display font-bold mb-3 uppercase tracking-widest">
            Impact Assessment
          </h4>
          <div className="flex items-start gap-4">
            <span
              className={`inline-flex items-center px-3 py-1 text-sm font-semibold ${getSeverityColor(impactAssessment.severity)}`}
            >
              {impactAssessment.severity}
            </span>
            <p className="text-sm font-body leading-relaxed flex-1">
              {impactAssessment.explanation}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIIntelligence;

