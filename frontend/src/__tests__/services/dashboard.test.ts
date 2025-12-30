/**
 * Dashboard Service Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getDashboardStats, getRecentChanges } from '../../services/dashboard';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
  getToken: vi.fn(),
  setToken: vi.fn(),
  removeToken: vi.fn(),
}));

describe('Dashboard Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDashboardStats', () => {
    it('should fetch dashboard statistics', async () => {
      const mockStats = {
        totalRoutes: 5,
        totalSources: 10,
        activeSources: 8,
        changesLast7Days: 3,
        changesLast30Days: 12,
        recentChanges: [],
        sourceHealth: [],
      };

      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockStats,
      } as any);

      const result = await getDashboardStats();

      expect(apiClient.get).toHaveBeenCalledWith('/api/dashboard');
      expect(result).toEqual(mockStats);
    });

    it('should return null on error', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('API Error'));

      const result = await getDashboardStats();

      expect(result).toBeNull();
    });
  });

  describe('getRecentChanges', () => {
    it('should fetch recent changes with default limit', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 3,
        pages: 0,
      };

      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockResponse,
      } as any);

      const result = await getRecentChanges();

      expect(apiClient.get).toHaveBeenCalledWith('/api/changes', {
        params: {
          page: 1,
          page_size: 3,
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch recent changes with custom limit', async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        page_size: 5,
        pages: 0,
      };

      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockResponse,
      } as any);

      const result = await getRecentChanges(5);

      expect(apiClient.get).toHaveBeenCalledWith('/api/changes', {
        params: {
          page: 1,
          page_size: 5,
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should return null on error', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('API Error'));

      const result = await getRecentChanges();

      expect(result).toBeNull();
    });
  });
});

