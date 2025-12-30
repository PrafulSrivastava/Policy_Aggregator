/**
 * System Settings Page Component
 * Configure system settings with feature toggles and compliance acknowledgments
 */

import React, { useState, useEffect } from 'react';
import { getSettings, saveSettings, type SystemSettings } from '../../services/settings';
import Toggle from '../../components/forms/Toggle';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';

const System: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings>({
    aiSummarization: true,
    impactScoring: true,
    liabilityAcknowledged: false,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [liabilityAcknowledged, setLiabilityAcknowledged] = useState<boolean>(false);

  /**
   * Load settings on mount
   */
  useEffect(() => {
    const loadSettings = (): void => {
      setLoading(true);
      setError(null);

      try {
        const currentSettings = getSettings();
        setSettings(currentSettings);
        setLiabilityAcknowledged(currentSettings.liabilityAcknowledged);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load settings';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, []);

  /**
   * Handle toggle change
   */
  const handleToggleChange = (key: 'aiSummarization' | 'impactScoring', value: boolean): void => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
    // Clear success message when settings change
    setSuccessMessage(null);
  };

  /**
   * Handle liability acknowledgment checkbox change
   */
  const handleLiabilityAcknowledgmentChange = (checked: boolean): void => {
    setLiabilityAcknowledged(checked);
    setSettings((prev) => ({
      ...prev,
      liabilityAcknowledged: checked,
    }));
    // Clear success message when settings change
    setSuccessMessage(null);
  };

  /**
   * Validate form before saving
   */
  const validateForm = (): boolean => {
    if (!liabilityAcknowledged) {
      setError('You must acknowledge the liability protocol before saving settings');
      return false;
    }
    return true;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!validateForm()) {
      return;
    }

    setSaving(true);

    try {
      // Simulate API call delay (remove in production if using real API)
      await new Promise((resolve) => setTimeout(resolve, 500));

      const settingsToSave: SystemSettings = {
        ...settings,
        liabilityAcknowledged: liabilityAcknowledged,
      };

      saveSettings(settingsToSave);
      setSuccessMessage('Settings saved successfully');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccessMessage(null);
      }, 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <LoadingSpinner message="Loading settings..." />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold mb-2">System Settings</h1>
        <p className="text-mutedForeground">
          Configure system features and acknowledge compliance protocols
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <ErrorMessage
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="card bg-black text-white p-4">
          <div className="flex items-center justify-between">
            <span className="font-semibold">{successMessage}</span>
            <button
              type="button"
              onClick={() => setSuccessMessage(null)}
              className="text-white hover:underline"
            >
              ×
            </button>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Feature Toggles Section */}
        <div className="card space-y-6">
          <h2 className="text-xl font-display font-semibold uppercase tracking-widest">
            Feature Toggles
          </h2>

          <div className="space-y-6">
            <Toggle
              id="ai-summarization"
              label="AI Summarization"
              checked={settings.aiSummarization}
              onChange={(checked) => handleToggleChange('aiSummarization', checked)}
              description="Enable AI-powered summarization of policy changes"
            />

            <Toggle
              id="impact-scoring"
              label="Impact Scoring"
              checked={settings.impactScoring}
              onChange={(checked) => handleToggleChange('impactScoring', checked)}
              description="Enable impact scoring for policy changes"
            />
          </div>
        </div>

        {/* Compliance Section */}
        <div className="card space-y-6">
          <h2 className="text-xl font-display font-semibold uppercase tracking-widest">
            Compliance
          </h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-display font-semibold mb-3">Liability Protocol</h3>
              <div className="prose prose-sm max-w-none text-mutedForeground space-y-2">
                <p>
                  By using this system, you acknowledge that:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Policy information is provided for informational purposes only</li>
                  <li>You are responsible for verifying all information independently</li>
                  <li>The system does not provide legal advice</li>
                  <li>You assume all liability for decisions made based on this information</li>
                </ul>
              </div>
            </div>

            <div className="pt-4 border-t border-foreground">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={liabilityAcknowledged}
                  onChange={(e) => handleLiabilityAcknowledgmentChange(e.target.checked)}
                  className="mt-1 mr-3 w-5 h-5 border-2 border-foreground rounded-none accent-foreground cursor-pointer"
                  required
                />
                <span className="text-sm font-medium uppercase tracking-widest">
                  I Acknowledge
                </span>
              </label>
              {!liabilityAcknowledged && (
                <p className="mt-2 text-sm text-red-500">
                  You must acknowledge the liability protocol to save settings
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving || !liabilityAcknowledged}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Commit Changes'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default System;

