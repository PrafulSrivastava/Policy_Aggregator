/**
 * API Client Tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { getToken, setToken, removeToken, getErrorMessage, isApiError } from '../services/api';
import type { AxiosError } from 'axios';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('API Client', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Token Management', () => {
    it('should store and retrieve token', () => {
      const token = 'test-token-123';
      setToken(token);
      expect(getToken()).toBe(token);
    });

    it('should return null when no token exists', () => {
      expect(getToken()).toBeNull();
    });

    it('should remove token', () => {
      setToken('test-token');
      removeToken();
      expect(getToken()).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('should identify API errors', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'TEST_ERROR',
              message: 'Test error message',
            },
          },
        },
      } as AxiosError;

      expect(isApiError(error)).toBe(true);
    });

    it('should extract error message from API error', () => {
      const error = {
        response: {
          data: {
            error: {
              code: 'TEST_ERROR',
              message: 'Test error message',
            },
          },
        },
      } as AxiosError;

      expect(getErrorMessage(error)).toBe('Test error message');
    });

    it('should handle non-API errors', () => {
      const error = new Error('Generic error');
      expect(getErrorMessage(error)).toBe('Generic error');
    });

    it('should handle unknown error types', () => {
      expect(getErrorMessage('string error')).toBe('An unexpected error occurred');
    });
  });
});

