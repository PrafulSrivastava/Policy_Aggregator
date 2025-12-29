/**
 * Authentication Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { login, logout, getCurrentUser } from '../services/auth';
import { apiClient, setToken } from '../services/api';

// Mock axios
vi.mock('axios');
vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...actual,
    apiClient: {
      post: vi.fn(),
      get: vi.fn(),
    },
  };
});

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

describe('Authentication Service', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('should successfully login with valid credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token-123',
          token_type: 'bearer',
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await login('testuser', 'password123');

      expect(result.success).toBe(true);
      expect(result.error).toBeUndefined();
      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        username: 'testuser',
        password: 'password123',
      });
    });

    it('should handle login failure', async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: 'INVALID_CREDENTIALS',
              message: 'Incorrect username or password',
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      const result = await login('testuser', 'wrongpassword');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Incorrect username or password');
    });

    it('should handle network errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      const result = await login('testuser', 'password123');

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('logout', () => {
    it('should successfully logout', async () => {
      setToken('test-token');
      vi.mocked(apiClient.post).mockResolvedValue({ data: { message: 'Logged out successfully' } });

      await logout();

      expect(apiClient.post).toHaveBeenCalledWith('/auth/logout');
      expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('should clear token even if API call fails', async () => {
      setToken('test-token');
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      await logout();

      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should return user data if endpoint exists', async () => {
      const mockUser = {
        id: '123',
        username: 'testuser',
        is_active: true,
      };

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser });

      const user = await getCurrentUser();

      expect(user).toEqual(mockUser);
      expect(apiClient.get).toHaveBeenCalledWith('/auth/me');
    });

    it('should return null if endpoint does not exist', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Not found'));

      const user = await getCurrentUser();

      expect(user).toBeNull();
    });
  });
});

