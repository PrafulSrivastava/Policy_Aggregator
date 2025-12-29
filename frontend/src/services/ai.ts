/**
 * AI Service
 * Handles API calls for AI-generated summaries
 */

import { apiClient, getErrorMessage, isApiError } from './api';

/**
 * AI summary response type
 */
export interface AISummaryResponse {
  summary: string;
  generated_at: string;
}

/**
 * Generate AI summary for route changes
 * 
 * @param routeId - Route ID
 * @returns AISummaryResponse with summary and timestamp
 * @throws Error if API call fails or service unavailable
 */
export const generateRouteSummary = async (
  routeId: string
): Promise<AISummaryResponse> => {
  try {
    const response = await apiClient.post<AISummaryResponse>(
      `/api/routes/${routeId}/summary`,
      {}
    );

    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 501 Not Implemented - AI service not available
      if (status === 501) {
        const errorMessage = errorData?.message || 'AI summary service is not available';
        const notImplementedError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
        };
        notImplementedError.code = 'NOT_IMPLEMENTED';
        notImplementedError.status = 501;
        throw notImplementedError;
      }

      // 404 Not Found - Route not found
      if (status === 404) {
        const errorMessage = errorData?.message || 'Route not found';
        const notFoundError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
        };
        notFoundError.code = 'ROUTE_NOT_FOUND';
        notFoundError.status = 404;
        throw notFoundError;
      }

      // 401 Unauthorized - handled by interceptor, but throw for completeness
      if (status === 401) {
        const errorMessage = errorData?.message || 'Unauthorized';
        const authError = new Error(errorMessage) as Error & { code: string; status: number };
        authError.code = 'UNAUTHORIZED';
        authError.status = 401;
        throw authError;
      }

      // Other errors
      const errorMessage = errorData?.message || 'Failed to generate AI summary';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

