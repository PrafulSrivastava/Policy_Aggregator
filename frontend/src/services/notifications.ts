/**
 * Notifications Service
 * Handles API calls for email notification settings
 */

import { apiClient, getErrorMessage, isApiError } from './api';

/**
 * Notification settings data type
 */
export interface NotificationSettings {
  enabled: boolean;
  frequency?: string;
  email?: string;
  updated_at?: string;
}

/**
 * Update notification settings request
 */
export interface UpdateNotificationSettingsRequest {
  enabled: boolean;
  frequency?: string;
  email?: string;
}

/**
 * Get current notification settings
 * 
 * @returns NotificationSettings with current configuration
 * @throws Error if API call fails or service unavailable
 */
export const getNotificationSettings = async (): Promise<NotificationSettings> => {
  try {
    const response = await apiClient.get<NotificationSettings>('/api/notifications/email');

    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 501 Not Implemented - Notification service not available
      if (status === 501) {
        const errorMessage = errorData?.message || 'Notification settings service is not available';
        const notImplementedError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
        };
        notImplementedError.code = 'NOT_IMPLEMENTED';
        notImplementedError.status = 501;
        throw notImplementedError;
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
      const errorMessage = errorData?.message || 'Failed to fetch notification settings';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

/**
 * Update notification settings
 * 
 * @param settings - Notification settings to update
 * @returns Updated NotificationSettings
 * @throws Error if API call fails or service unavailable
 */
export const updateNotificationSettings = async (
  settings: UpdateNotificationSettingsRequest
): Promise<NotificationSettings> => {
  try {
    const response = await apiClient.post<NotificationSettings>(
      '/api/notifications/email',
      settings
    );

    return response.data;
  } catch (error) {
    // Handle specific error cases
    if (isApiError(error)) {
      const status = error.response?.status;
      const errorData = error.response?.data?.error;

      // 501 Not Implemented - Notification service not available
      if (status === 501) {
        const errorMessage = errorData?.message || 'Notification settings service is not available';
        const notImplementedError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
        };
        notImplementedError.code = 'NOT_IMPLEMENTED';
        notImplementedError.status = 501;
        throw notImplementedError;
      }

      // 400 Bad Request - Validation errors
      if (status === 400) {
        const errorMessage = errorData?.message || 'Validation error';
        const validationError = new Error(errorMessage) as Error & { 
          code: string; 
          status: number;
          details?: unknown;
        };
        validationError.code = 'VALIDATION_ERROR';
        validationError.status = 400;
        validationError.details = errorData?.details;
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
      const errorMessage = errorData?.message || 'Failed to update notification settings';
      throw new Error(errorMessage);
    }

    throw new Error(getErrorMessage(error));
  }
};

