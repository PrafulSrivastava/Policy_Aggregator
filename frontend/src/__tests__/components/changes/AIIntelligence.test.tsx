/**
 * AI Intelligence Component Tests
 * Tests AI intelligence component rendering and functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AIIntelligence from '../../../components/changes/AIIntelligence';
import type { PolicyChangeDetail } from '../../../services/changes';
import * as aiService from '../../../services/ai';

// Mock the AI service
vi.mock('../../../services/ai', () => ({
  generateRouteSummary: vi.fn(),
}));

describe('AIIntelligence', () => {
  const mockChange: PolicyChangeDetail = {
    id: 'change-1',
    detected_at: '2025-01-27T10:00:00Z',
    summary: 'Policy content updated',
    is_new: true,
    diff_length: 250,
    diff: 'Sample diff text',
    source: {
      id: 'source-1',
      name: 'Germany Student Visa Source',
      url: 'https://example.com/policy',
      country: 'DE',
      visa_type: 'Student',
    },
    route: {
      id: 'route-1',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      display: 'IN → DE, Student',
    },
    old_version: null,
    new_version: {
      id: 'version-1',
      content_hash: 'hash1',
      raw_text: 'New content',
      fetched_at: '2025-01-27T10:00:00Z',
      content_length: 100,
    },
    previous_change_id: null,
    next_change_id: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state while generating AI summary', () => {
    vi.mocked(aiService.generateRouteSummary).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<AIIntelligence change={mockChange} />);

    expect(screen.getByText(/Generating AI summary/i)).toBeInTheDocument();
  });

  it('should display AI summary when available', async () => {
    const mockSummary: aiService.AISummaryResponse = {
      summary: 'This policy change updates student visa requirements with new documentation needs.',
      generated_at: '2025-01-27T10:05:00Z',
    };

    vi.mocked(aiService.generateRouteSummary).mockResolvedValue(mockSummary);

    render(<AIIntelligence change={mockChange} />);

    await waitFor(() => {
      expect(screen.getByText(/AI Intelligence/i)).toBeInTheDocument();
      expect(screen.getByText(/Synthesis/i)).toBeInTheDocument();
    });
  });

  it('should display impact assessment', () => {
    render(<AIIntelligence change={mockChange} />);

    expect(screen.getByText(/Impact Assessment/i)).toBeInTheDocument();
    expect(screen.getByText(/Medium|High|Low/i)).toBeInTheDocument();
  });

  it('should handle AI service not available gracefully', async () => {
    const notImplementedError = new Error('AI service not available') as Error & {
      code: string;
      status: number;
    };
    notImplementedError.code = 'NOT_IMPLEMENTED';
    notImplementedError.status = 501;

    vi.mocked(aiService.generateRouteSummary).mockRejectedValue(notImplementedError);

    render(<AIIntelligence change={mockChange} />);

    await waitFor(() => {
      // Should not show error, just not show summary
      expect(screen.queryByText(/Failed to generate/i)).not.toBeInTheDocument();
    });
  });

  it('should display message when change has no route', () => {
    const changeWithoutRoute: PolicyChangeDetail = {
      ...mockChange,
      route: null,
    };

    render(<AIIntelligence change={changeWithoutRoute} />);

    expect(screen.getByText(/AI summary is not available for changes without an associated route/i)).toBeInTheDocument();
  });

  it('should calculate impact assessment based on diff length', () => {
    const highImpactChange: PolicyChangeDetail = {
      ...mockChange,
      diff_length: 600,
    };

    render(<AIIntelligence change={highImpactChange} />);

    expect(screen.getByText(/High/i)).toBeInTheDocument();
  });
});

