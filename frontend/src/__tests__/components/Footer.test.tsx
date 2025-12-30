/**
 * Footer Component Tests
 * Tests footer rendering and system status marquee
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Footer from '../../components/Footer';
import { getStatus } from '../../services/api';

// Mock the API service
vi.mock('../../services/api', () => ({
  getStatus: vi.fn(),
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

describe('Footer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render footer', () => {
    vi.mocked(getStatus).mockResolvedValue({
      sources: [],
      statistics: {
        total_sources: 0,
        healthy_sources: 0,
        error_sources: 0,
        stale_sources: 0,
        never_checked_sources: 0,
      },
      last_daily_job_run: null,
    });

    render(<Footer />);
    
    expect(document.querySelector('footer')).toBeInTheDocument();
  });

  it('should display loading status initially', () => {
    vi.mocked(getStatus).mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<Footer />);
    
    expect(screen.getByText(/Loading system status/i)).toBeInTheDocument();
  });

  it('should display system status after fetching', async () => {
    const mockStatus = {
      sources: [],
      statistics: {
        total_sources: 10,
        healthy_sources: 8,
        error_sources: 1,
        stale_sources: 1,
        never_checked_sources: 0,
      },
      last_daily_job_run: null,
    };

    vi.mocked(getStatus).mockResolvedValue(mockStatus);

    render(<Footer />);

    await waitFor(() => {
      expect(screen.getByText(/Total Sources: 10/i)).toBeInTheDocument();
      expect(screen.getByText(/Healthy: 8/i)).toBeInTheDocument();
    });
  });

  it('should refresh status every 30 seconds', async () => {
    const mockStatus = {
      sources: [],
      statistics: {
        total_sources: 5,
        healthy_sources: 5,
        error_sources: 0,
        stale_sources: 0,
        never_checked_sources: 0,
      },
      last_daily_job_run: null,
    };

    vi.mocked(getStatus).mockResolvedValue(mockStatus);

    render(<Footer />);

    await waitFor(() => {
      expect(getStatus).toHaveBeenCalledTimes(1);
    });

    // Advance time by 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(getStatus).toHaveBeenCalledTimes(2);
    });
  });

  it('should handle API errors gracefully', async () => {
    vi.mocked(getStatus).mockRejectedValue(new Error('API Error'));

    render(<Footer />);

    await waitFor(() => {
      // Should still render footer even on error
      expect(document.querySelector('footer')).toBeInTheDocument();
    });
  });
});

