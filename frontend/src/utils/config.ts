/**
 * Application configuration
 * Reads from environment variables with Vite prefix
 */

export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
} as const;

