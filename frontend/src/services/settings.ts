/**
 * Settings Service
 * Handles system settings persistence using localStorage
 */

export interface SystemSettings {
  aiSummarization: boolean;
  impactScoring: boolean;
  liabilityAcknowledged: boolean;
  liabilityAcknowledgedAt?: string;
}

const SETTINGS_STORAGE_KEY = 'policy_aggregator_system_settings';

/**
 * Default system settings
 */
const DEFAULT_SETTINGS: SystemSettings = {
  aiSummarization: true,
  impactScoring: true,
  liabilityAcknowledged: false,
};

/**
 * Get system settings from localStorage
 * 
 * @returns SystemSettings object with current settings
 */
export const getSettings = (): SystemSettings => {
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as Partial<SystemSettings>;
      return {
        ...DEFAULT_SETTINGS,
        ...parsed,
      };
    }
  } catch (error) {
    console.error('Failed to load settings from localStorage:', error);
  }
  
  return { ...DEFAULT_SETTINGS };
};

/**
 * Save system settings to localStorage
 * 
 * @param settings - SystemSettings object to save
 * @throws Error if save fails
 */
export const saveSettings = (settings: SystemSettings): void => {
  try {
    const settingsToSave: SystemSettings = {
      ...settings,
      liabilityAcknowledgedAt: settings.liabilityAcknowledged
        ? new Date().toISOString()
        : undefined,
    };
    
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settingsToSave));
  } catch (error) {
    console.error('Failed to save settings to localStorage:', error);
    throw new Error('Failed to save settings');
  }
};

/**
 * Reset settings to defaults
 */
export const resetSettings = (): void => {
  try {
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to reset settings:', error);
  }
};

