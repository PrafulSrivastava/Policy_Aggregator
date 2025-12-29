/**
 * Changes Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getChanges, getChangesForRoute, getChangeDetail } from '../../services/changes';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    get: vi.fn(),
  },
  getErrorMessage: (error: unknown) => {
    if (error instanceof Error) return error.message;
    return 'An unexpected error occurred';
  },
  isApiError: (error: unknown) => {
    return error && typeof error === 'object' && 'response' in error;
  },
}));

describe('Changes Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getChanges', () => {
    it('should fetch changes with default pagination', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '123',
              detected_at: '2025-01-27T10:00:00Z',
              summary: 'Content changed',
              is_new: true,
              diff_length: 150,
              source: {
                id: '456',
                name: 'Test Source',
                url: 'https://example.com',
                country: 'DE',
                visa_type: 'Student',
              },
              route: {
                id: '789',
                origin_country: 'IN',
                destination_country: 'DE',
                visa_type: 'Student',
                display: 'IN → DE, Student',
              },
            },
          ],
          total: 1,
          page: 1,
          page_size: 50,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getChanges();

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/changes', {
        params: {
          page: 1,
          page_size: 50,
        },
      });
    });

    it('should fetch changes with filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 50,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getChanges(1, 50, {
        route_id: 'route-123',
        source_id: 'source-456',
        start_date: '2025-01-01',
        end_date: '2025-01-31',
      });

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/changes', {
        params: {
          page: 1,
          page_size: 50,
          route_id: 'route-123',
          source_id: 'source-456',
          start_date: '2025-01-01',
          end_date: '2025-01-31',
        },
      });
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'API_ERROR',
              message: 'Failed to fetch changes',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(getChanges()).rejects.toThrow('Failed to fetch changes');
    });
  });

  describe('getChangesForRoute', () => {
    it('should fetch changes filtered by route', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 50,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getChangesForRoute('route-123');

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/changes', {
        params: {
          page: 1,
          page_size: 50,
          route_id: 'route-123',
        },
      });
    });
  });

  describe('getChangeDetail', () => {
    it('should fetch change detail successfully', async () => {
      const mockResponse = {
        data: {
          id: '123',
          detected_at: '2025-01-27T10:00:00Z',
          summary: 'Content changed',
          is_new: true,
          diff_length: 150,
          diff: '--- old\n+++ new\n@@ -1,3 +1,3 @@\n line1\n-line2\n+line2new\n line3',
          source: {
            id: '456',
            name: 'Test Source',
            url: 'https://example.com',
            country: 'DE',
            visa_type: 'Student',
          },
          route: {
            id: '789',
            origin_country: 'IN',
            destination_country: 'DE',
            visa_type: 'Student',
            display: 'IN → DE, Student',
          },
          old_version: {
            id: 'old-123',
            content_hash: 'abc123',
            raw_text: 'old content',
            fetched_at: '2025-01-26T10:00:00Z',
            content_length: 100,
          },
          new_version: {
            id: 'new-123',
            content_hash: 'def456',
            raw_text: 'new content',
            fetched_at: '2025-01-27T10:00:00Z',
            content_length: 120,
          },
          previous_change_id: null,
          next_change_id: null,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getChangeDetail('123');

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/changes/123');
    });

    it('should handle 404 error', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'CHANGE_NOT_FOUND',
              message: 'Change not found',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      try {
        await getChangeDetail('123');
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Change not found');
        expect(err.code).toBe('CHANGE_NOT_FOUND');
        expect(err.status).toBe(404);
      }
    });
  });
});

