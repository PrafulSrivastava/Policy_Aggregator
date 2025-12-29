/**
 * AI Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { generateRouteSummary } from '../../services/ai';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    post: vi.fn(),
  },
  getErrorMessage: (error: unknown) => {
    if (error instanceof Error) return error.message;
    return 'An unexpected error occurred';
  },
  isApiError: (error: unknown) => {
    return error && typeof error === 'object' && 'response' in error;
  },
}));

describe('AI Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('generateRouteSummary', () => {
    it('should generate summary successfully', async () => {
      const routeId = '123e4567-e89b-12d3-a456-426614174000';
      const mockResponse = {
        data: {
          summary: 'Key Changes: Updated visa requirements. Impact: Affects student visa applications. Context: Policy change effective immediately.',
          generated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await generateRouteSummary(routeId);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith(
        `/api/routes/${routeId}/summary`,
        {}
      );
    });

    it('should handle 501 Not Implemented error', async () => {
      const routeId = '123e4567-e89b-12d3-a456-426614174000';
      const mockError = {
        response: {
          status: 501,
          data: {
            error: {
              code: 'NOT_IMPLEMENTED',
              message: 'AI summary service is not available',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await generateRouteSummary(routeId);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('AI summary service is not available');
        expect(err.code).toBe('NOT_IMPLEMENTED');
        expect(err.status).toBe(501);
      }
    });

    it('should handle 404 Not Found error', async () => {
      const routeId = 'invalid-route-id';
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'ROUTE_NOT_FOUND',
              message: 'Route not found',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await generateRouteSummary(routeId);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Route not found');
        expect(err.code).toBe('ROUTE_NOT_FOUND');
        expect(err.status).toBe(404);
      }
    });

    it('should handle 401 Unauthorized error', async () => {
      const routeId = '123e4567-e89b-12d3-a456-426614174000';
      const mockError = {
        response: {
          status: 401,
          data: {
            error: {
              code: 'UNAUTHORIZED',
              message: 'Unauthorized',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await generateRouteSummary(routeId);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Unauthorized');
        expect(err.code).toBe('UNAUTHORIZED');
        expect(err.status).toBe(401);
      }
    });

    it('should handle generic API errors', async () => {
      const routeId = '123e4567-e89b-12d3-a456-426614174000';
      const mockError = {
        response: {
          status: 500,
          data: {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'Internal server error',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await generateRouteSummary(routeId);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect((error as Error).message).toBe('Internal server error');
      }
    });

    it('should handle network errors', async () => {
      const routeId = '123e4567-e89b-12d3-a456-426614174000';

      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      await expect(generateRouteSummary(routeId)).rejects.toThrow();
    });
  });
});

