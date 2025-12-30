/**
 * Changes Service
 * Handles API calls for policy changes and diffs
 */

import { apiClient, getErrorMessage, isApiError } from './api';

/**
 * Source information in change response
 */
export interface ChangeSource {
  id: string;
  name: string;
  url: string;
  country: string;
  visa_type: string;
}

/**
 * Route information in change response
 */
export interface ChangeRoute {
  id: string;
  origin_country: string;
  destination_country: string;
  visa_type: string;
  display: string;
}

/**
 * Policy version information
 */
export interface PolicyVersion {
  id: string;
  content_hash: string;
  raw_text: string;
  fetched_at: string;
  content_length: number;
}

/**
 * Policy change data type (list item)
 */
export interface PolicyChange {
  id: string;
  detected_at: string;
  summary: string;
  is_new: boolean;
  diff_length: number;
  source: ChangeSource;
  route: ChangeRoute | null;
}

/**
 * Policy change detail (full change with diff)
 */
export interface PolicyChangeDetail extends PolicyChange {
  diff: string;
  old_version: PolicyVersion | null;
  new_version: PolicyVersion;
  previous_change_id: string | null;
  next_change_id: string | null;
}

/**
 * Paginated changes response
 */
export interface PaginatedChangesResponse {
  items: PolicyChange[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
}

/**
 * Get changes with pagination and optional filters
 * 
 * @param page - Page number (1-indexed, default: 1)
 * @param pageSize - Number of items per page (default: 50, max: 100)
 * @param filters - Optional filters (route_id, source_id, start_date, end_date)
 * @returns PaginatedChangesResponse with changes and metadata
 * @throws Error if API call fails
 */
export const getChanges = async (
  page: number = 1,
  pageSize: number = 50,
  filters?: {
    route_id?: string;
    source_id?: string;
    start_date?: string;
    end_date?: string;
  }
): Promise<PaginatedChangesResponse> => {
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: pageSize,
    };

    if (filters?.route_id) {
      params.route_id = filters.route_id;
    }
    if (filters?.source_id) {
      params.source_id = filters.source_id;
    }
    if (filters?.start_date) {
      params.start_date = filters.start_date;
    }
    if (filters?.end_date) {
      params.end_date = filters.end_date;
    }

    const response = await apiClient.get<PaginatedChangesResponse>('/api/changes', {
      params,
    });

    return response.data;
  } catch (error) {
    // Re-throw with a more descriptive error message
    if (isApiError(error)) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to fetch changes';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Get changes for a specific route
 * 
 * @param routeId - Route ID
 * @param page - Page number (1-indexed, default: 1)
 * @param pageSize - Number of items per page (default: 50)
 * @returns PaginatedChangesResponse with changes for the route
 * @throws Error if API call fails
 */
export const getChangesForRoute = async (
  routeId: string,
  page: number = 1,
  pageSize: number = 50
): Promise<PaginatedChangesResponse> => {
  return getChanges(page, pageSize, {
    route_id: routeId,
  });
};

/**
 * Get detailed information for a specific change
 * 
 * @param changeId - Change ID
 * @returns PolicyChangeDetail with full diff and version information
 * @throws Error if API call fails
 */
export const getChangeDetail = async (
  changeId: string
): Promise<PolicyChangeDetail> => {
  try {
    const response = await apiClient.get<PolicyChangeDetail>(`/api/changes/${changeId}`);
    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 404 Not Found
      if (status === 404) {
        const errorMessage = errorData?.message || 'Change not found';
        const notFoundError = new Error(errorMessage) as Error & { code: string; status: number };
        notFoundError.code = 'CHANGE_NOT_FOUND';
        notFoundError.status = 404;
        throw notFoundError;
      }

      // Other errors
      const errorMessage = errorData?.message || 'Failed to fetch change detail';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};


