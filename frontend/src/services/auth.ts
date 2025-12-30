/**
 * Authentication service
 * Handles login, logout, and user authentication operations
 */

import { apiClient, getErrorMessage, isApiError } from './api';
import { setToken, removeToken } from './api';

/**
 * Login request payload
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Login response payload
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

/**
 * Login result
 */
export interface LoginResult {
  success: boolean;
  error?: string;
}

/**
 * Mock credentials for demonstration
 */
const MOCK_CREDENTIALS = {
  username: 'admin@example.com',
  password: 'password',
};

/**
 * Check if mock authentication is enabled
 */
const isMockAuthEnabled = (): boolean => {
  return import.meta.env.VITE_MOCK_AUTH === 'true' || import.meta.env.VITE_MOCK_AUTH === '1';
};

/**
 * Simulate network delay
 */
const delay = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Log in with username and password
 * Supports both mock authentication and real API authentication
 * 
 * @param username - User's username
 * @param password - User's password
 * @returns LoginResult with success status and optional error message
 */
export const login = async (username: string, password: string): Promise<LoginResult> => {
  // Check if mock authentication is enabled
  if (isMockAuthEnabled()) {
    // Simulate network latency (1.5s delay)
    await delay(1500);

    // Check against hardcoded credentials
    if (username === MOCK_CREDENTIALS.username && password === MOCK_CREDENTIALS.password) {
      // Set a mock token for consistency
      setToken('mock-token-' + Date.now());
      return { success: true };
    } else {
      return { success: false, error: 'Access Denied' };
    }
  }

  // Real API authentication
  try {
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      username,
      password,
    } as LoginRequest);

    // Store the token
    if (response.data.access_token) {
      setToken(response.data.access_token);
    }

    return { success: true };
  } catch (error) {
    // Handle API errors
    if (isApiError(error)) {
      const errorMessage = error.response?.data?.error?.message || 'Login failed';
      return { success: false, error: errorMessage };
    }

    // Handle network errors
    return { success: false, error: getErrorMessage(error) };
  }
};

/**
 * Log out the current user
 * 
 * @returns Promise that resolves when logout is complete
 */
export const logout = async (): Promise<void> => {
  try {
    // Call logout endpoint to invalidate token on server
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Even if the API call fails, clear the token locally
    // This ensures the user is logged out even if the server is unreachable
    console.error('Logout API call failed:', error);
  } finally {
    // Always clear the token from storage
    removeToken();
  }
};

/**
 * Get current user information (if endpoint exists)
 * This is optional - the backend may not have a /auth/me endpoint
 * 
 * @returns User information or null if not available
 */
export const getCurrentUser = async (): Promise<unknown | null> => {
  try {
    const response = await apiClient.get('/auth/me');
    return response.data;
  } catch {
    // Endpoint may not exist, return null
    return null;
  }
};

/**
 * OAuth login functions (if backend supports)
 * These are placeholders for future OAuth implementation
 */

/**
 * Initiate Google OAuth login
 * 
 * @returns OAuth URL or null if not supported
 */
export const loginWithGoogle = async (): Promise<string | null> => {
  // TODO: Implement when backend supports Google OAuth
  // This would typically redirect to Google's OAuth page
  return null;
};

/**
 * Initiate GitHub OAuth login
 * 
 * @returns OAuth URL or null if not supported
 */
export const loginWithGitHub = async (): Promise<string | null> => {
  // TODO: Implement when backend supports GitHub OAuth
  // This would typically redirect to GitHub's OAuth page
  return null;
};

