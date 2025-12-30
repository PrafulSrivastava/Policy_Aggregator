/**
 * Base API client service
 * Handles all HTTP requests with authentication token management
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios';
import { config } from '../utils/config';

// Token storage key
const TOKEN_STORAGE_KEY = 'access_token';

/**
 * Get stored authentication token
 */
export const getToken = (): string | null => {
  // Try to get from localStorage first
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    return token;
  }
  
  // Try to get from httpOnly cookie (if available)
  // Note: httpOnly cookies are not accessible via JavaScript
  // The backend sets the cookie, but we also store in localStorage as fallback
  return null;
};

/**
 * Store authentication token
 */
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
};

/**
 * Remove authentication token
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
};

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const apiClient = axios.create({
    baseURL: config.apiBaseUrl,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // Important for httpOnly cookies
  });

  // Request interceptor: Attach auth token to requests
  apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = getToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor: Handle 401 errors and redirect to login
  apiClient.interceptors.response.use(
    (response: AxiosResponse) => {
      return response;
    },
    (error: AxiosError) => {
      // Handle 401 Unauthorized - redirect to login
      if (error.response?.status === 401) {
        // Clear invalid token
        removeToken();
        
        // Only redirect if we're not already on the login page
        if (window.location.pathname !== '/login') {
          // Store the intended destination
          const currentPath = window.location.pathname;
          window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
        }
      }
      
      return Promise.reject(error);
    }
  );

  return apiClient;
};

// Export the configured API client instance
export const apiClient = createApiClient();

/**
 * API error response type
 */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
    timestamp?: string;
    requestId?: string;
  };
}

/**
 * Check if error is an API error
 */
export const isApiError = (error: unknown): error is AxiosError<ApiError> => {
  return axios.isAxiosError(error) && error.response?.data?.error !== undefined;
};

/**
 * Extract error message from API error
 */
export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    return error.response?.data?.error?.message || 'An error occurred';
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

/**
 * Get system status
 */
export const getStatus = async (): Promise<unknown> => {
  const response = await apiClient.get('/api/status');
  return response.data;
};

