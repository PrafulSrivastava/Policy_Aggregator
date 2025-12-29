/**
 * Notifications Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getNotificationSettings, updateNotificationSettings } from '../../services/notifications';
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

describe('Notifications Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getNotificationSettings', () => {
    it('should fetch notification settings successfully', async () => {
      const mockResponse = {
        data: {
          enabled: true,
          frequency: 'immediate',
          email: 'user@example.com',
          updated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await getNotificationSettings();

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.get).toHaveBeenCalledWith('/api/notifications/email');
    });

    it('should handle 501 Not Implemented error', async () => {
      const mockError = {
        response: {
          status: 501,
          data: {
            error: {
              code: 'NOT_IMPLEMENTED',
              message: 'Notification settings service is not available',
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      try {
        await getNotificationSettings();
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Notification settings service is not available');
        expect(err.code).toBe('NOT_IMPLEMENTED');
        expect(err.status).toBe(501);
      }
    });

    it('should handle 401 Unauthorized error', async () => {
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

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      try {
        await getNotificationSettings();
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
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

      await expect(getNotificationSettings()).rejects.toThrow();
    });
  });

  describe('updateNotificationSettings', () => {
    it('should update notification settings successfully', async () => {
      const settings = {
        enabled: true,
        frequency: 'daily',
        email: 'user@example.com',
      };

      const mockResponse = {
        data: {
          enabled: true,
          frequency: 'daily',
          email: 'user@example.com',
          updated_at: '2025-01-27T10:00:00Z',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await updateNotificationSettings(settings);

      expect(result).toEqual(mockResponse.data);
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/notifications/email',
        settings
      );
    });

    it('should handle 501 Not Implemented error', async () => {
      const settings = {
        enabled: true,
        frequency: 'immediate',
        email: 'user@example.com',
      };

      const mockError = {
        response: {
          status: 501,
          data: {
            error: {
              code: 'NOT_IMPLEMENTED',
              message: 'Notification settings service is not available',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await updateNotificationSettings(settings);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { code?: string; status?: number };
        expect(err.message).toBe('Notification settings service is not available');
        expect(err.code).toBe('NOT_IMPLEMENTED');
        expect(err.status).toBe(501);
      }
    });

    it('should handle 400 Validation error', async () => {
      const settings = {
        enabled: true,
        frequency: 'invalid',
        email: 'invalid-email',
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
                frequency: ['Invalid frequency value'],
              },
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      try {
        await updateNotificationSettings(settings);
        expect.fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        const err = error as Error & { 
          code?: string; 
          status?: number; 
          details?: unknown;
        };
        expect(err.message).toBe('Validation failed');
        expect(err.code).toBe('VALIDATION_ERROR');
        expect(err.status).toBe(400);
        expect(err.details).toEqual({
          email: ['Invalid email format'],
          frequency: ['Invalid frequency value'],
        });
      }
    });

    it('should handle network errors', async () => {
      const settings = {
        enabled: true,
        frequency: 'immediate',
        email: 'user@example.com',
      };

      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      await expect(updateNotificationSettings(settings)).rejects.toThrow();
    });
  });
});

