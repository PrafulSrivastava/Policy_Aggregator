/**
 * Dashboard Page Component Tests
 * Tests enhanced dashboard with marquee, recent signals, and quick actions
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import Dashboard from '../../pages/Dashboard';
import * as dashboardService from '../../services/dashboard';

// Mock the dashboard service
vi.mock('../../services/dashboard', () => ({
  getDashboardStats: vi.fn(),
  getRecentChanges: vi.fn(),
}));

// Mock the auth service
vi.mock('../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
  logout: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API client
vi.mock('../../services/api', () => ({
  getToken: vi.fn().mockReturnValue(null),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <HashRouter>
    {children}
  </HashRouter>
);

describe('Dashboard Page', () => {
  const mockDashboardStats = {
    totalRoutes: 5,
    totalSources: 10,
    activeSources: 8,
    changesLast7Days: 3,
    changesLast30Days: 12,
    recentChanges: [],
    sourceHealth: [],
  };

  const mockRecentChanges = {
    items: [
      {
        id: '1',
        detected_at: '2025-01-27T10:00:00Z',
        source: {
          id: 'source-1',
          name: 'Germany Student Visa',
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
        summary: 'Content changed',
        is_new: true,
        diff_length: 150,
      },
    ],
    total: 1,
    page: 1,
    page_size: 3,
    pages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render loading state initially', () => {
    vi.mocked(dashboardService.getDashboardStats).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  it('should render dashboard with statistics', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(mockDashboardStats);
    vi.mocked(dashboardService.getRecentChanges).mockResolvedValue(mockRecentChanges);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText(/total routes: 5/i)).toBeInTheDocument();
    expect(screen.getByText(/active sources: 8/i)).toBeInTheDocument();
  });

  it('should render recent signals feed', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(mockDashboardStats);
    vi.mocked(dashboardService.getRecentChanges).mockResolvedValue(mockRecentChanges);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Recent Signals')).toBeInTheDocument();
      expect(screen.getByText('Germany Student Visa')).toBeInTheDocument();
    });
  });

  it('should render quick actions cards', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(mockDashboardStats);
    vi.mocked(dashboardService.getRecentChanges).mockResolvedValue(mockRecentChanges);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Route Index')).toBeInTheDocument();
      expect(screen.getByText('Source Nodes')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument(); // Total routes
      expect(screen.getByText('8')).toBeInTheDocument(); // Active sources
    });
  });

  it('should handle error state', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(null);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard statistics/i)).toBeInTheDocument();
    });
  });

  it('should refresh statistics every 30 seconds', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue(mockDashboardStats);
    vi.mocked(dashboardService.getRecentChanges).mockResolvedValue(mockRecentChanges);

    render(
      <TestWrapper>
        <Dashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(dashboardService.getDashboardStats).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 30 seconds
    vi.advanceTimersByTime(30000);

    await waitFor(() => {
      expect(dashboardService.getDashboardStats).toHaveBeenCalledTimes(2);
    });
  });
});

