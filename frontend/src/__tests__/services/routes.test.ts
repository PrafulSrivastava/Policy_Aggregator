/**
 * Routes Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getRoutes, createRoute } from '../../services/routes';
import { apiClient } from '../../services/api';

// Mock the API client
vi.mock('../../services/api', () => ({
  apiClient: {
    get: vi.fn(),
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

describe('Routes Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getRoutes', () => {
    it('should fetch routes with default pagination', async () => {
      const mockResponse = {
        data: {
          items: [
            {
              id: '123',
              origin_country: 'IN',
              destination_country: 'DE',
              visa_type: 'Student',
              email: 'user@example.com',
              is_active: true,
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

      const result = await getRoutes();

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/routes', {
        params: {
          page: 1,
          page_size: 20,
        },
      });
    });

    it('should fetch routes with custom pagination', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 2,
          page_size: 10,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getRoutes(2, 10);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/routes', {
        params: {
          page: 2,
          page_size: 10,
        },
      });
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'API_ERROR',
              message: 'Failed to fetch routes',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(getRoutes()).rejects.toThrow('Failed to fetch routes');
    });

    it('should handle network errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

      await expect(getRoutes()).rejects.toThrow();
    });
  });

  describe('createRoute', () => {
    it('should create a route successfully', async () => {
      const mockRouteData = {
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      };

      const mockResponse = {
        data: {
          id: '123',
          origin_country: 'IN',
          destination_country: 'DE',
          visa_type: 'Student',
          email: 'user@example.com',
          is_active: true,
          created_at: '2025-01-27T10:00:00Z',
          updated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await createRoute(mockRouteData);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith('/api/routes', {
        origin_country: 'IN',
        destination_country: 'DE',
        visa_type: 'Student',
        email: 'user@example.com',
      });
    });

    it('should handle duplicate route error (409)', async () => {
      const mockRouteData = {
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      };

      const mockError = {
        response: {
          status: 409,
          data: {
            error: {
              code: 'DUPLICATE_ROUTE',
              message: 'This route already exists',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await createRoute(mockRouteData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('This route already exists');
        expect(err.code).toBe('DUPLICATE_ROUTE');
        expect(err.status).toBe(409);
      }
    });

    it('should handle validation errors (400)', async () => {
      const mockRouteData = {
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      };

      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Validation failed',
              details: {
                email: ['Invalid email format'],
                origin_country: ['Country code must be 2 characters'],
              },
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await createRoute(mockRouteData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number; details?: unknown };
        expect(err.message).toBe('Validation failed');
        expect(err.code).toBe('VALIDATION_ERROR');
        expect(err.status).toBe(400);
        expect(err.details).toEqual({
          email: ['Invalid email format'],
          origin_country: ['Country code must be 2 characters'],
        });
      }
    });

    it('should handle unauthorized error (401)', async () => {
      const mockRouteData = {
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      };

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
        await createRoute(mockRouteData);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Unauthorized');
        expect(err.code).toBe('UNAUTHORIZED');
        expect(err.status).toBe(401);
      }
    });

    it('should handle network errors', async () => {
      const mockRouteData = {
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      };

      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      await expect(createRoute(mockRouteData)).rejects.toThrow();
    });
  });
});

