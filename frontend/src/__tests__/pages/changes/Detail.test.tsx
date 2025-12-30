/**
 * Change Detail Page Tests
 * Tests change detail page functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ChangeDetail from '../../../pages/changes/Detail';
import * as changesService from '../../../services/changes';
import * as aiService from '../../../services/ai';

// Mock the changes service
vi.mock('../../../services/changes', () => ({
  getChangeDetail: vi.fn(),
}));

// Mock the AI service
vi.mock('../../../services/ai', () => ({
  generateRouteSummary: vi.fn(),
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ changeId: 'change-1' }),
  };
});

describe('Change Detail Page', () => {
  const mockChangeDetail: changesService.PolicyChangeDetail = {
    id: 'change-1',
    detected_at: '2025-01-27T10:00:00Z',
    summary: 'Policy content updated',
    is_new: true,
    diff_length: 250,
    diff: '--- old\n+++ new\n@@ -1,2 +1,3 @@\n line1\n+line2\n line3',
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

  it('should display loading state while fetching change', () => {
    vi.mocked(changesService.getChangeDetail).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    expect(screen.getByText(/Loading change/i)).toBeInTheDocument();
  });

  it('should display change detail with enhanced header', async () => {
    vi.mocked(changesService.getChangeDetail).mockResolvedValue(mockChangeDetail);

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/IN → DE/i)).toBeInTheDocument();
      expect(screen.getByText(/Student/i)).toBeInTheDocument();
      expect(screen.getByText(/Germany Student Visa Source/i)).toBeInTheDocument();
    });
  });

  it('should display AI Intelligence section', async () => {
    vi.mocked(changesService.getChangeDetail).mockResolvedValue(mockChangeDetail);
    // Mock AI service to resolve quickly
    vi.mocked(aiService.generateRouteSummary).mockResolvedValue({
      summary: 'AI summary text',
      generated_at: '2025-01-27T10:05:00Z',
    });

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/AI Intelligence/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Impact Assessment should always be visible
    expect(screen.getByText(/Impact Assessment/i)).toBeInTheDocument();
  });

  it('should display Export Tools section', async () => {
    vi.mocked(changesService.getChangeDetail).mockResolvedValue(mockChangeDetail);

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Export Tools/i)).toBeInTheDocument();
      expect(screen.getByText(/Source Link/i)).toBeInTheDocument();
      expect(screen.getByText(/Export JSON/i)).toBeInTheDocument();
    });
  });

  it('should display diff viewer', async () => {
    vi.mocked(changesService.getChangeDetail).mockResolvedValue(mockChangeDetail);

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Diff/i)).toBeInTheDocument();
      expect(screen.getByText(/line2/)).toBeInTheDocument();
    });
  });

  it('should display error message when change not found', async () => {
    const notFoundError = new Error('Change not found') as Error & { code?: string };
    notFoundError.code = 'CHANGE_NOT_FOUND';
    vi.mocked(changesService.getChangeDetail).mockRejectedValue(notFoundError);

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Change not found/i)).toBeInTheDocument();
      expect(screen.getByText(/Back to Changes/i)).toBeInTheDocument();
    });
  });

  it('should handle change without route gracefully', async () => {
    const changeWithoutRoute: changesService.PolicyChangeDetail = {
      ...mockChangeDetail,
      route: null,
    };

    vi.mocked(changesService.getChangeDetail).mockResolvedValue(changeWithoutRoute);

    render(
      <MemoryRouter>
        <ChangeDetail />
      </MemoryRouter>
    );

    await waitFor(() => {
      // Should still render, just without route-specific features
      expect(screen.getByText(/Germany Student Visa Source/i)).toBeInTheDocument();
    });
  });
});

