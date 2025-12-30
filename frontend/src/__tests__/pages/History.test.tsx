/**
 * Changes/History Page Tests
 * Tests change history list page functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Changes from '../../pages/Changes';
import * as changesService from '../../services/changes';

// Mock the changes service
vi.mock('../../services/changes', () => ({
  getChanges: vi.fn(),
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Changes Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading spinner while fetching changes', () => {
    vi.mocked(changesService.getChanges).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    // Loading spinner should be visible
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('should display changes list when data is loaded', async () => {
    const mockChanges = [
      {
        id: 'change-1',
        detected_at: '2025-01-27T10:00:00Z',
        summary: 'Policy content updated',
        is_new: true,
        diff_length: 150,
        source: {
          id: 'source-1',
          name: 'Germany Student Visa Source',
          url: 'https://example.com',
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
      },
    ];

    vi.mocked(changesService.getChanges).mockResolvedValue({
      items: mockChanges,
      total: 1,
      page: 1,
      page_size: 50,
      pages: 1,
    });

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Change History')).toBeInTheDocument();
      expect(screen.getByText('Germany Student Visa Source')).toBeInTheDocument();
      expect(screen.getByText('Policy content updated')).toBeInTheDocument();
    });
  });

  it('should display error message when API call fails', async () => {
    vi.mocked(changesService.getChanges).mockRejectedValue(
      new Error('Failed to fetch changes')
    );

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch changes/i)).toBeInTheDocument();
      expect(screen.getByText(/Retry/i)).toBeInTheDocument();
    });
  });

  it('should display empty state when no changes found', async () => {
    vi.mocked(changesService.getChanges).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      pages: 0,
    });

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No changes found/i)).toBeInTheDocument();
    });
  });

  it('should navigate to change detail when Analyze Diff is clicked', async () => {
    const mockChanges = [
      {
        id: 'change-1',
        detected_at: '2025-01-27T10:00:00Z',
        summary: 'Policy content updated',
        is_new: true,
        diff_length: 150,
        source: {
          id: 'source-1',
          name: 'Germany Student Visa Source',
          url: 'https://example.com',
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
      },
    ];

    vi.mocked(changesService.getChanges).mockResolvedValue({
      items: mockChanges,
      total: 1,
      page: 1,
      page_size: 50,
      pages: 1,
    });

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Analyze Diff')).toBeInTheDocument();
    });

    const analyzeButton = screen.getByText('Analyze Diff');
    analyzeButton.click();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/changes/change-1');
    });
  });

  it('should display pagination when there are multiple pages', async () => {
    const mockChanges = Array.from({ length: 50 }, (_, i) => ({
      id: `change-${i}`,
      detected_at: '2025-01-27T10:00:00Z',
      summary: `Change ${i}`,
      is_new: false,
      diff_length: 100,
      source: {
        id: 'source-1',
        name: 'Test Source',
        url: 'https://example.com',
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
    }));

    vi.mocked(changesService.getChanges).mockResolvedValue({
      items: mockChanges,
      total: 100,
      page: 1,
      page_size: 50,
      pages: 2,
    });

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Previous')).toBeInTheDocument();
    });
  });

  it('should retry fetching when retry button is clicked', async () => {
    vi.mocked(changesService.getChanges).mockRejectedValueOnce(
      new Error('Failed to fetch changes')
    );

    render(
      <MemoryRouter>
        <Changes />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Retry/i)).toBeInTheDocument();
    });

    // Mock successful response for retry
    vi.mocked(changesService.getChanges).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      pages: 0,
    });

    const retryButton = screen.getByText(/Retry/i);
    retryButton.click();

    await waitFor(() => {
      expect(changesService.getChanges).toHaveBeenCalledTimes(2);
    });
  });
});

