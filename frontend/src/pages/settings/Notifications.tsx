/**
 * Notification Settings Page Component
 * Configure email notification preferences
 */

import React, { useState, useEffect } from 'react';
import { 
  getNotificationSettings, 
  updateNotificationSettings
} from '../../services/notifications';
import type {
  NotificationSettings,
  UpdateNotificationSettingsRequest
} from '../../services/notifications';
import Select from '../../components/forms/Select';
import EmailInput from '../../components/forms/EmailInput';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';

interface FormErrors {
  email?: string;
  frequency?: string;
  general?: string;
}

const FREQUENCY_OPTIONS = [
  { value: 'immediate', label: 'Immediate' },
  { value: 'daily', label: 'Daily Digest' },
  { value: 'weekly', label: 'Weekly Digest' },
];

const Notifications: React.FC = () => {
  const [settings, setSettings] = useState<NotificationSettings>({
    enabled: false,
    frequency: 'immediate',
    email: '',
  });
  const [formData, setFormData] = useState<UpdateNotificationSettingsRequest>({
    enabled: false,
    frequency: 'immediate',
    email: '',
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  /**
   * Fetch current notification settings
   */
  useEffect(() => {
    const fetchSettings = async (): Promise<void> => {
      setLoading(true);
      setError(null);

      try {
        const currentSettings = await getNotificationSettings();
        setSettings(currentSettings);
        setFormData({
          enabled: currentSettings.enabled ?? false,
          frequency: currentSettings.frequency ?? 'immediate',
          email: currentSettings.email ?? '',
        });
      } catch (err) {
        const errorWithCode = err as Error & { code?: string; status?: number };
        
        // Handle 501 Not Implemented gracefully
        if (errorWithCode.code === 'NOT_IMPLEMENTED' || errorWithCode.status === 501) {
          setError('Notification settings service is not available. The backend endpoint may not be implemented yet.');
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load notification settings';
          setError(errorMessage);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // If enabled, email is required
    if (formData.enabled && !formData.email) {
      newErrors.email = 'Email is required when notifications are enabled';
    } else if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Frequency is required if enabled
    if (formData.enabled && !formData.frequency) {
      newErrors.frequency = 'Frequency is required when notifications are enabled';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    // Clear previous errors and success message
    setErrors({});
    setError(null);
    setSuccessMessage(null);

    // Validate form
    if (!validateForm()) {
      return;
    }

    setSaving(true);

    try {
      const updatedSettings = await updateNotificationSettings(formData);
      setSettings(updatedSettings);
      setFormData({
        enabled: updatedSettings.enabled,
        frequency: updatedSettings.frequency ?? 'immediate',
        email: updatedSettings.email ?? '',
      });
      setSuccessMessage('Notification settings saved successfully');
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setSuccessMessage(null);
      }, 5000);
    } catch (err) {
      const errorWithCode = err as Error & { code?: string; status?: number; details?: unknown };
      
      // Handle 501 Not Implemented gracefully
      if (errorWithCode.code === 'NOT_IMPLEMENTED' || errorWithCode.status === 501) {
        setError('Notification settings service is not available. The backend endpoint may not be implemented yet.');
      } else if (errorWithCode.code === 'VALIDATION_ERROR' && errorWithCode.details) {
        // Handle validation errors
        const fieldErrors: FormErrors = {};
        const details = errorWithCode.details as { [key: string]: string[] };
        
        if (details.email) {
          fieldErrors.email = details.email[0];
        }
        if (details.frequency) {
          fieldErrors.frequency = details.frequency[0];
        }
        
        setErrors(fieldErrors);
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Failed to save notification settings';
        setError(errorMessage);
      }
    } finally {
      setSaving(false);
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof UpdateNotificationSettingsRequest) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ): void => {
    const value = e.target.type === 'checkbox' 
      ? (e.target as HTMLInputElement).checked 
      : e.target.value;

    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear success message when user makes changes
    if (successMessage) {
      setSuccessMessage(null);
    }
  };

  /**
   * Handle toggle change
   */
  const handleToggle = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setFormData((prev) => ({
      ...prev,
      enabled: e.target.checked,
    }));

    // Clear errors when toggling
    setErrors({});
    setSuccessMessage(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-2xl mx-auto">
          <LoadingSpinner message="Loading notification settings..." />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-7xl font-display font-bold mb-8 tracking-tight">
          Notification Settings
        </h1>

        {/* Error Message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mb-6 p-4 border-2 border-foreground bg-background">
            <p className="text-sm font-body text-green-600">{successMessage}</p>
          </div>
        )}

        {/* Current Status */}
        <div className="mb-6 p-4 border-2 border-foreground bg-background">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-display font-bold mb-1 uppercase tracking-widest">
                Current Status
              </h2>
              <p className="text-sm font-body">
                Notifications are{' '}
                <span className={`font-bold ${settings.enabled ? 'text-green-600' : 'text-mutedForeground'}`}>
                  {settings.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </p>
              {settings.enabled && settings.frequency && (
                <p className="text-xs text-mutedForeground mt-1">
                  Frequency: {FREQUENCY_OPTIONS.find(opt => opt.value === settings.frequency)?.label || settings.frequency}
                </p>
              )}
              {settings.updated_at && (
                <p className="text-xs text-mutedForeground mt-1 font-mono">
                  Last updated: {new Date(settings.updated_at).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Settings Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Enable/Disable Toggle */}
            <div>
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={handleToggle}
                  className="mr-3 w-5 h-5 border-2 border-foreground accent-foreground"
                  disabled={saving}
                />
                <span className="text-sm font-medium uppercase tracking-widest">
                  Enable Email Notifications
                </span>
              </label>
              <p className="text-xs text-mutedForeground mt-2 ml-8">
                Receive email alerts when policy changes are detected for your routes
              </p>
            </div>

            {/* Email Address */}
            {formData.enabled && (
              <EmailInput
                id="email"
                label="Email Address"
                required={formData.enabled}
                value={formData.email}
                onChange={handleChange('email')}
                error={errors.email}
                disabled={saving}
                placeholder="Enter email address for notifications"
              />
            )}

            {/* Frequency */}
            {formData.enabled && (
              <Select
                id="frequency"
                label="Notification Frequency"
                required={formData.enabled}
                options={FREQUENCY_OPTIONS}
                value={formData.frequency || 'immediate'}
                onChange={handleChange('frequency')}
                error={errors.frequency}
                disabled={saving}
              />
            )}

            {/* Form Actions */}
            <div className="flex items-center space-x-4 pt-4">
              <button
                type="submit"
                className="btn-primary"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Notifications;

