/**
 * Sources Service
 * Handles API calls for source management
 */

import { apiClient, getErrorMessage, isApiError } from './api';

/**
 * Source data type
 */
export interface Source {
  id: string;
  country: string;
  visa_type: string;
  url: string;
  name: string;
  fetch_type: 'html' | 'pdf';
  check_frequency: 'daily' | 'weekly' | 'custom';
  is_active: boolean;
  last_checked_at: string | null;
  last_change_detected_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  status?: 'healthy' | 'stale' | 'error' | 'never_checked';
  consecutive_fetch_failures?: number;
  last_fetch_error?: string | null;
}

/**
 * Paginated sources response
 */
export interface PaginatedSourcesResponse {
  items: Source[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Create source request data type
 */
export interface CreateSourceRequest {
  country: string;
  visaType: string;
  url: string;
  name: string;
  fetchType: 'html' | 'pdf';
  checkFrequency: 'daily' | 'weekly' | 'custom';
  isActive?: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * Get sources with pagination and optional filters
 * 
 * @param page - Page number (1-indexed, default: 1)
 * @param pageSize - Number of items per page (default: 20, max: 100)
 * @param filters - Optional filters (country, visa_type, is_active)
 * @returns PaginatedSourcesResponse with sources and metadata
 * @throws Error if API call fails
 */
export const getSources = async (
  page: number = 1,
  pageSize: number = 20,
  filters?: {
    country?: string;
    visa_type?: string;
    is_active?: boolean;
  }
): Promise<PaginatedSourcesResponse> => {
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: pageSize,
    };

    if (filters?.country) {
      params.country = filters.country;
    }
    if (filters?.visa_type) {
      params.visa_type = filters.visa_type;
    }
    if (filters?.is_active !== undefined) {
      params.is_active = filters.is_active;
    }

    const response = await apiClient.get<PaginatedSourcesResponse>('/api/sources', {
      params,
    });

    return response.data;
  } catch (error) {
    // Re-throw with a more descriptive error message
    if (isApiError(error)) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to fetch sources';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Get sources for a specific route (filtered by country and visa_type)
 * 
 * @param routeId - Route ID (for metadata tracking, optional)
 * @param country - Destination country code
 * @param visaType - Visa type
 * @param page - Page number (1-indexed, default: 1)
 * @param pageSize - Number of items per page (default: 20)
 * @returns PaginatedSourcesResponse with sources matching the route
 * @throws Error if API call fails
 */
export const getSourcesForRoute = async (
  country: string,
  visaType: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PaginatedSourcesResponse> => {
  return getSources(page, pageSize, {
    country: country.toUpperCase(),
    visa_type: visaType,
  });
};

/**
 * Create a new source
 * 
 * @param sourceData - Source data to create
 * @returns Created Source
 * @throws Error if API call fails with specific error details
 */
export const createSource = async (
  sourceData: CreateSourceRequest
): Promise<Source> => {
  try {
    const response = await apiClient.post<Source>('/api/sources', {
      country: sourceData.country.toUpperCase(),
      visa_type: sourceData.visaType,
      url: sourceData.url,
      name: sourceData.name,
      fetch_type: sourceData.fetchType,
      check_frequency: sourceData.checkFrequency,
      is_active: sourceData.isActive !== undefined ? sourceData.isActive : true,
      metadata: sourceData.metadata || {},
    });

    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 409 Conflict - Duplicate source
      if (status === 409) {
        const errorMessage = errorData?.message || 'This source already exists';
        const duplicateError = new Error(errorMessage) as Error & { code: string; status: number };
        duplicateError.code = 'DUPLICATE_SOURCE';
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
      const errorMessage = errorData?.message || 'Failed to create source';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Create a source and associate it with a route (via metadata)
 * 
 * @param routeId - Route ID to associate with
 * @param sourceData - Source data to create
 * @returns Created Source
 * @throws Error if API call fails
 */
export const addSourceToRoute = async (
  routeId: string,
  sourceData: CreateSourceRequest
): Promise<Source> => {
  // Store route_id in metadata for explicit tracking
  const metadata = {
    ...sourceData.metadata,
    route_id: routeId,
  };

  return createSource({
    ...sourceData,
    metadata,
  });
};

/**
 * Update source request data type
 */
export interface UpdateSourceRequest {
  country?: string;
  visaType?: string;
  url?: string;
  name?: string;
  fetchType?: 'html' | 'pdf';
  checkFrequency?: 'daily' | 'weekly' | 'custom';
  isActive?: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * Update an existing source
 * 
 * @param sourceId - Source ID to update
 * @param sourceData - Source data to update
 * @returns Updated Source
 * @throws Error if API call fails
 */
export const updateSource = async (
  sourceId: string,
  sourceData: UpdateSourceRequest
): Promise<Source> => {
  try {
    const updatePayload: Record<string, unknown> = {};
    
    if (sourceData.country !== undefined) {
      updatePayload.country = sourceData.country.toUpperCase();
    }
    if (sourceData.visaType !== undefined) {
      updatePayload.visa_type = sourceData.visaType;
    }
    if (sourceData.url !== undefined) {
      updatePayload.url = sourceData.url;
    }
    if (sourceData.name !== undefined) {
      updatePayload.name = sourceData.name;
    }
    if (sourceData.fetchType !== undefined) {
      updatePayload.fetch_type = sourceData.fetchType;
    }
    if (sourceData.checkFrequency !== undefined) {
      updatePayload.check_frequency = sourceData.checkFrequency;
    }
    if (sourceData.isActive !== undefined) {
      updatePayload.is_active = sourceData.isActive;
    }
    if (sourceData.metadata !== undefined) {
      updatePayload.metadata = sourceData.metadata;
    }

    const response = await apiClient.put<Source>(`/api/sources/${sourceId}`, updatePayload);

    return response.data;
  } catch (error) {
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      if (status === 404) {
        const errorMessage = errorData?.message || 'Source not found';
        throw new Error(errorMessage);
      }

      if (status === 400) {
        const errorMessage = errorData?.message || 'Validation error';
        throw new Error(errorMessage);
      }

      const errorMessage = errorData?.message || 'Failed to update source';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Trigger source fetch response type
 */
export interface TriggerSourceResponse {
  success: boolean;
  sourceId: string;
  changeDetected: boolean;
  policyVersionId: string | null;
  policyChangeId: string | null;
  error: string | null;
  fetchedAt: string | null;
}

/**
 * Manually trigger a source fetch
 * 
 * @param sourceId - Source ID to trigger
 * @returns TriggerSourceResponse with fetch result
 * @throws Error if API call fails
 */
export const triggerSourceFetch = async (
  sourceId: string
): Promise<TriggerSourceResponse> => {
  try {
    const response = await apiClient.post<TriggerSourceResponse>(
      `/api/sources/${sourceId}/trigger`
    );

    return response.data;
  } catch (error) {
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      if (status === 404) {
        const errorMessage = errorData?.message || 'Source not found';
        throw new Error(errorMessage);
      }

      const errorMessage = errorData?.message || 'Failed to trigger source fetch';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * System status response with sources
 */
export interface SystemStatusResponse {
  sources: Source[];
  statistics: {
    total_sources: number;
    healthy_sources: number;
    error_sources: number;
    stale_sources: number;
    never_checked_sources: number;
  };
  last_daily_job_run: string | null;
}

/**
 * Get system status with all sources and their health information
 * 
 * @returns SystemStatusResponse with sources and statistics
 * @throws Error if API call fails
 */
export const getSystemStatus = async (): Promise<SystemStatusResponse> => {
  try {
    const response = await apiClient.get<SystemStatusResponse>('/api/status');
    return response.data;
  } catch (error) {
    if (isApiError(error)) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to fetch system status';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

