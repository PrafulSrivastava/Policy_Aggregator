/**
 * Dashboard service
 * Handles fetching dashboard statistics and recent changes
 */

import { apiClient, getErrorMessage } from './api';

/**
 * Dashboard statistics response
 */
export interface DashboardStats {
  totalRoutes: number;
  totalSources: number;
  activeSources: number;
  changesLast7Days: number;
  changesLast30Days: number;
  recentChanges: Array<{
    id: string;
    sourceId: string;
    sourceName: string;
    route: string;
    detectedAt: string;
    hasDiff: boolean;
    diffLength: number;
  }>;
  sourceHealth: Array<{
    sourceId: string;
    sourceName: string;
    country: string;
    visaType: string;
    lastCheckedAt: string | null;
    status: string;
    consecutiveFailures: number;
    lastError: string | null;
  }>;
}

/**
 * Change item from changes API
 */
export interface ChangeItem {
  id: string;
  detected_at: string;
  source: {
    id: string;
    name: string;
    country: string;
    visa_type: string;
  };
  route: {
    id: string;
    origin_country: string;
    destination_country: string;
    visa_type: string;
    display: string;
  };
  summary: string;
  is_new: boolean;
  diff_length: number;
}

/**
 * Paginated changes response
 */
export interface PaginatedChangesResponse {
  items: ChangeItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/**
 * Get dashboard statistics
 * 
 * @returns DashboardStats or null if error
 */
export const getDashboardStats = async (): Promise<DashboardStats | null> => {
  try {
    const response = await apiClient.get<DashboardStats>('/api/dashboard');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', getErrorMessage(error));
    return null;
  }
};

/**
 * Get recent changes
 * 
 * @param limit - Number of changes to fetch (default: 3)
 * @returns PaginatedChangesResponse or null if error
 */
export const getRecentChanges = async (limit: number = 3): Promise<PaginatedChangesResponse | null> => {
  try {
    const response = await apiClient.get<PaginatedChangesResponse>('/api/changes', {
      params: {
        page: 1,
        page_size: limit,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch recent changes:', getErrorMessage(error));
    return null;
  }
};

