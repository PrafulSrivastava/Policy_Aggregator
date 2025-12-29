/**
 * Routes Service
 * Handles API calls for route subscriptions
 */

import { apiClient, getErrorMessage, isApiError } from './api';

/**
 * Route subscription data type
 */
export interface RouteSubscription {
  id: string;
  origin_country: string;
  destination_country: string;
  visa_type: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Paginated routes response
 */
export interface PaginatedRoutesResponse {
  items: RouteSubscription[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Create route request data type
 */
export interface CreateRouteRequest {
  originCountry: string;
  destinationCountry: string;
  visaType: string;
  email: string;
}

/**
 * Create route error response with field-specific errors
 */
export interface CreateRouteError {
  code: string;
  message: string;
  details?: {
    [key: string]: string[];
  };
}

/**
 * Get routes with pagination
 * 
 * @param page - Page number (1-indexed, default: 1)
 * @param pageSize - Number of items per page (default: 20, max: 100)
 * @returns PaginatedRoutesResponse with routes and metadata
 * @throws Error if API call fails
 */
export const getRoutes = async (
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedRoutesResponse> => {
  try {
    const response = await apiClient.get<PaginatedRoutesResponse>('/api/routes', {
      params: {
        page,
        page_size: pageSize,
      },
    });

    return response.data;
  } catch (error) {
    // Re-throw with a more descriptive error message
    if (isApiError(error)) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to fetch routes';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Create a new route subscription
 * 
 * @param routeData - Route data to create
 * @returns Created RouteSubscription
 * @throws Error if API call fails with specific error details
 */
export const createRoute = async (
  routeData: CreateRouteRequest
): Promise<RouteSubscription> => {
  try {
    const response = await apiClient.post<RouteSubscription>('/api/routes', {
      origin_country: routeData.originCountry,
      destination_country: routeData.destinationCountry,
      visa_type: routeData.visaType,
      email: routeData.email,
    });

    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 409 Conflict - Duplicate route
      if (status === 409) {
        const errorMessage = errorData?.message || 'This route already exists';
        const duplicateError = new Error(errorMessage) as Error & { code: string; status: number };
        duplicateError.code = 'DUPLICATE_ROUTE';
        duplicateError.status = 409;
        throw duplicateError;
      }

      // 400 Bad Request - Validation errors
      if (status === 400) {
        const errorMessage = errorData?.message || 'Validation error';
        const validationError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
          details?: { [key: string]: string[] };
        };
        validationError.code = 'VALIDATION_ERROR';
        validationError.status = 400;
        validationError.details = errorData?.details as { [key: string]: string[] } | undefined;
        throw validationError;
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
      const errorMessage = errorData?.message || 'Failed to create route';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

