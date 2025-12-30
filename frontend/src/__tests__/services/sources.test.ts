/**
 * Sources Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getSources, getSourcesForRoute, createSource, addSourceToRoute, updateSource, triggerSourceFetch, getSystemStatus } from '../../services/sources';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
  getErrorMessage: (error: unknown) => {
    if (error instanceof Error) return error.message;
    return 'An unexpected error occurred';
  },
  isApiError: (error: unknown) => {
    return error && typeof error === 'object' && 'response' in error;
  },
}));

describe('Sources Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getSources', () => {
    it('should fetch sources with default pagination', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '123',
              country: 'DE',
              visa_type: 'Student',
              url: 'https://example.com/policy',
              name: 'Test Source',
              fetch_type: 'html',
              check_frequency: 'daily',
              is_active: true,
              last_checked_at: null,
              last_change_detected_at: null,
              metadata: {},
              created_at: '2025-01-27T10:00:00Z',
              updated_at: '2025-01-27T10:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getSources();

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/sources', {
        params: {
          page: 1,
          page_size: 20,
        },
      });
    });

    it('should fetch sources with filters', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getSources(1, 20, {
        country: 'DE',
        visa_type: 'Student',
        is_active: true,
      });

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/sources', {
        params: {
          page: 1,
          page_size: 20,
          country: 'DE',
          visa_type: 'Student',
          is_active: true,
        },
      });
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'API_ERROR',
              message: 'Failed to fetch sources',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(getSources()).rejects.toThrow('Failed to fetch sources');
    });
  });

  describe('getSourcesForRoute', () => {
    it('should fetch sources filtered by country and visa type', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getSourcesForRoute('DE', 'Student');

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/sources', {
        params: {
          page: 1,
          page_size: 20,
          country: 'DE',
          visa_type: 'Student',
        },
      });
    });
  });

  describe('createSource', () => {
    it('should create a source successfully', async () => {
      const mockSourceData = {
        country: 'DE',
        visaType: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetchType: 'html' as const,
        checkFrequency: 'daily' as const,
      };

      const mockResponse = {
        data: {
          id: '123',
          country: 'DE',
          visa_type: 'Student',
          url: 'https://example.com/policy',
          name: 'Test Source',
          fetch_type: 'html',
          check_frequency: 'daily',
          is_active: true,
          last_checked_at: null,
          last_change_detected_at: null,
          metadata: {},
          created_at: '2025-01-27T10:00:00Z',
          updated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await createSource(mockSourceData);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith('/api/sources', {
        country: 'DE',
        visa_type: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetch_type: 'html',
        check_frequency: 'daily',
        is_active: true,
        metadata: {},
      });
    });

    it('should handle duplicate source error (409)', async () => {
      const mockSourceData = {
        country: 'DE',
        visaType: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetchType: 'html' as const,
        checkFrequency: 'daily' as const,
      };

      const mockError = {
        response: {
          status: 409,
          data: {
            error: {
              code: 'DUPLICATE_SOURCE',
              message: 'This source already exists',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await createSource(mockSourceData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('This source already exists');
        expect(err.code).toBe('DUPLICATE_SOURCE');
        expect(err.status).toBe(409);
      }
    });

    it('should handle validation errors (400)', async () => {
      const mockSourceData = {
        country: 'DE',
        visaType: 'Student',
        url: 'invalid-url',
        name: 'Test Source',
        fetchType: 'html' as const,
        checkFrequency: 'daily' as const,
      };

      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Validation failed',
              details: {
                url: ['Invalid URL format'],
              },
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await createSource(mockSourceData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number; details?: unknown };
        expect(err.message).toBe('Validation failed');
        expect(err.code).toBe('VALIDATION_ERROR');
        expect(err.status).toBe(400);
        expect(err.details).toEqual({
          url: ['Invalid URL format'],
        });
      }
    });
  });

  describe('addSourceToRoute', () => {
    it('should create source with route_id in metadata', async () => {
      const mockSourceData = {
        country: 'DE',
        visaType: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetchType: 'html' as const,
        checkFrequency: 'daily' as const,
      };

      const mockResponse = {
        data: {
          id: '123',
          country: 'DE',
          visa_type: 'Student',
          url: 'https://example.com/policy',
          name: 'Test Source',
          fetch_type: 'html',
          check_frequency: 'daily',
          is_active: true,
          last_checked_at: null,
          last_change_detected_at: null,
          metadata: { route_id: 'route-123' },
          created_at: '2025-01-27T10:00:00Z',
          updated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await addSourceToRoute('route-123', mockSourceData);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith('/api/sources', {
        country: 'DE',
        visa_type: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetch_type: 'html',
        check_frequency: 'daily',
        is_active: true,
        metadata: { route_id: 'route-123' },
      });
    });
  });

  describe('updateSource', () => {
    it('should update a source successfully', async () => {
      const mockUpdateData = {
        name: 'Updated Source',
        url: 'https://example.com/updated',
      };

      const mockResponse = {
        data: {
          id: '123',
          country: 'DE',
          visa_type: 'Student',
          url: 'https://example.com/updated',
          name: 'Updated Source',
          fetch_type: 'html',
          check_frequency: 'daily',
          is_active: true,
          last_checked_at: null,
          last_change_detected_at: null,
          metadata: {},
          created_at: '2025-01-27T10:00:00Z',
          updated_at: '2025-01-27T11:00:00Z',
        },
      };

      vi.mocked(apiClient.put).mockResolvedValue(mockResponse);

      const result = await updateSource('123', mockUpdateData);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.put).toHaveBeenCalledWith('/api/sources/123', {
        name: 'Updated Source',
        url: 'https://example.com/updated',
      });
    });

    it('should handle 404 error when source not found', async () => {
      const mockUpdateData = {
        name: 'Updated Source',
      };

      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'SOURCE_NOT_FOUND',
              message: 'Source not found',
            },
          },
        },
      };

      vi.mocked(apiClient.put).mockRejectedValue(mockError);

      await expect(updateSource('123', mockUpdateData)).rejects.toThrow('Source not found');
    });
  });

  describe('triggerSourceFetch', () => {
    it('should trigger source fetch successfully', async () => {
      const mockResponse = {
        data: {
          success: true,
          sourceId: '123',
          changeDetected: false,
          policyVersionId: 'version-1',
          policyChangeId: null,
          error: null,
          fetchedAt: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await triggerSourceFetch('123');

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith('/api/sources/123/trigger');
    });

    it('should handle fetch failure', async () => {
      const mockResponse = {
        data: {
          success: false,
          sourceId: '123',
          changeDetected: false,
          policyVersionId: null,
          policyChangeId: null,
          error: 'Fetch failed: Network error',
          fetchedAt: null,
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await triggerSourceFetch('123');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Fetch failed: Network error');
    });

    it('should handle 404 error when source not found', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'SOURCE_NOT_FOUND',
              message: 'Source not found',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(triggerSourceFetch('123')).rejects.toThrow('Source not found');
    });
  });

  describe('getSystemStatus', () => {
    it('should fetch system status with sources', async () => {
      const mockResponse = {
        data: {
          sources: [
            {
              id: '123',
              name: 'Test Source',
              country: 'DE',
              visa_type: 'Student',
              url: 'https://example.com/policy',
              fetch_type: 'html',
              check_frequency: 'daily',
              is_active: true,
              last_checked_at: '2025-01-27T10:00:00Z',
              last_change_detected_at: null,
              status: 'healthy',
              consecutive_fetch_failures: 0,
              last_fetch_error: null,
            },
          ],
          statistics: {
            total_sources: 1,
            healthy_sources: 1,
            error_sources: 0,
            stale_sources: 0,
            never_checked_sources: 0,
          },
          last_daily_job_run: null,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getSystemStatus();

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/status');
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'API_ERROR',
              message: 'Failed to fetch system status',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(getSystemStatus()).rejects.toThrow('Failed to fetch system status');
    });
  });
});

