/**
 * SummaryView Component
 * Displays AI-generated summary with sections for Key Changes, Impact, and Context
 */

import React from 'react';

interface SummaryViewProps {
  summary: string;
  generatedAt?: string;
  className?: string;
}

/**
 * Parse summary text into sections
 * Attempts to identify Key Changes, Impact, and Context sections
 */
const parseSummary = (summary: string): {
  keyChanges?: string;
  impact?: string;
  context?: string;
  raw: string;
} => {
  // Try to parse structured summary with sections
  const keyChangesMatch = summary.match(/(?:Key Changes?|Changes?|What Changed):\s*(.+?)(?:\n\n|Impact|Context|$)/is);
  const impactMatch = summary.match(/(?:Impact|Effect|Implications?):\s*(.+?)(?:\n\n|Context|Key Changes|$)/is);
  const contextMatch = summary.match(/(?:Context|Background|Details?):\s*(.+?)$/is);

  if (keyChangesMatch || impactMatch || contextMatch) {
    return {
      keyChanges: keyChangesMatch?.[1]?.trim(),
      impact: impactMatch?.[1]?.trim(),
      context: contextMatch?.[1]?.trim(),
      raw: summary,
    };
  }

  // If no structured sections found, return raw summary
  return {
    raw: summary,
  };
};

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

const SummaryView: React.FC<SummaryViewProps> = ({ 
  summary, 
  generatedAt,
  className = '' 
}) => {
  const parsed = parseSummary(summary);

  return (
    <div className={`border-2 border-foreground bg-background ${className}`}>
      <div className="p-6">
        {/* Header with AI disclaimer */}
        <div className="mb-6 pb-4 border-b-2 border-foreground">
          <h3 className="text-lg font-display font-bold mb-2 uppercase tracking-widest">
            AI-Generated Summary
          </h3>
          {generatedAt && (
            <p className="text-xs text-mutedForeground font-mono">
              Generated: {formatDate(generatedAt)}
            </p>
          )}
          <p className="text-xs text-mutedForeground italic mt-2">
            This summary is AI-generated and may contain inaccuracies. Please review the full diff for complete details.
          </p>
        </div>

        {/* Key Changes Section */}
        {parsed.keyChanges && (
          <div className="mb-6">
            <h4 className="text-sm font-display font-bold mb-3 uppercase tracking-widest">
              Key Changes
            </h4>
            <div className="text-sm font-body leading-relaxed whitespace-pre-wrap">
              {parsed.keyChanges}
            </div>
          </div>
        )}

        {/* Impact Section */}
        {parsed.impact && (
          <div className="mb-6">
            <h4 className="text-sm font-display font-bold mb-3 uppercase tracking-widest">
              Impact
            </h4>
            <div className="text-sm font-body leading-relaxed whitespace-pre-wrap">
              {parsed.impact}
            </div>
          </div>
        )}

        {/* Context Section */}
        {parsed.context && (
          <div className="mb-6">
            <h4 className="text-sm font-display font-bold mb-3 uppercase tracking-widest">
              Context
            </h4>
            <div className="text-sm font-body leading-relaxed whitespace-pre-wrap">
              {parsed.context}
            </div>
          </div>
        )}

        {/* Raw Summary (if no sections parsed or as fallback) */}
        {(!parsed.keyChanges && !parsed.impact && !parsed.context) && (
          <div className="text-sm font-body leading-relaxed whitespace-pre-wrap">
            {parsed.raw}
          </div>
        )}
      </div>
    </div>
  );
};

export default SummaryView;

