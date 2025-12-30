/**
 * Settings Service Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getSettings, saveSettings, resetSettings, type SystemSettings } from '../../services/settings';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string): string | null => store[key] || null,
    setItem: (key: string, value: string): void => {
      store[key] = value.toString();
    },
    removeItem: (key: string): void => {
      delete store[key];
    },
    clear: (): void => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Settings Service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('getSettings', () => {
    it('should return default settings when no settings are stored', () => {
      const settings = getSettings();

      expect(settings).toEqual({
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: false,
      });
    });

    it('should return stored settings when available', () => {
      const storedSettings: SystemSettings = {
        aiSummarization: false,
        impactScoring: true,
        liabilityAcknowledged: true,
        liabilityAcknowledgedAt: '2025-01-27T10:00:00Z',
      };

      localStorage.setItem('policy_aggregator_system_settings', JSON.stringify(storedSettings));

      const settings = getSettings();

      expect(settings).toEqual(storedSettings);
    });

    it('should merge stored settings with defaults for missing fields', () => {
      const partialSettings = {
        aiSummarization: false,
      };

      localStorage.setItem('policy_aggregator_system_settings', JSON.stringify(partialSettings));

      const settings = getSettings();

      expect(settings.aiSummarization).toBe(false);
      expect(settings.impactScoring).toBe(true); // Default
      expect(settings.liabilityAcknowledged).toBe(false); // Default
    });

    it('should handle invalid JSON gracefully', () => {
      localStorage.setItem('policy_aggregator_system_settings', 'invalid json');

      const settings = getSettings();

      // Should return defaults
      expect(settings).toEqual({
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: false,
      });
    });
  });

  describe('saveSettings', () => {
    it('should save settings to localStorage', () => {
      const settings: SystemSettings = {
        aiSummarization: false,
        impactScoring: true,
        liabilityAcknowledged: true,
      };

      saveSettings(settings);

      const stored = localStorage.getItem('policy_aggregator_system_settings');
      expect(stored).not.toBeNull();

      const parsed = JSON.parse(stored!);
      expect(parsed.aiSummarization).toBe(false);
      expect(parsed.impactScoring).toBe(true);
      expect(parsed.liabilityAcknowledged).toBe(true);
      expect(parsed.liabilityAcknowledgedAt).toBeDefined();
    });

    it('should set liabilityAcknowledgedAt when liability is acknowledged', () => {
      const settings: SystemSettings = {
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: true,
      };

      saveSettings(settings);

      const stored = localStorage.getItem('policy_aggregator_system_settings');
      const parsed = JSON.parse(stored!);
      
      expect(parsed.liabilityAcknowledgedAt).toBeDefined();
      expect(new Date(parsed.liabilityAcknowledgedAt).getTime()).toBeLessThanOrEqual(Date.now());
    });

    it('should not set liabilityAcknowledgedAt when liability is not acknowledged', () => {
      const settings: SystemSettings = {
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: false,
      };

      saveSettings(settings);

      const stored = localStorage.getItem('policy_aggregator_system_settings');
      const parsed = JSON.parse(stored!);
      
      expect(parsed.liabilityAcknowledgedAt).toBeUndefined();
    });

    it('should throw error when localStorage is unavailable', () => {
      // Mock localStorage.setItem to throw
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = vi.fn(() => {
        throw new Error('Storage quota exceeded');
      });

      const settings: SystemSettings = {
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: false,
      };

      expect(() => saveSettings(settings)).toThrow('Failed to save settings');

      // Restore
      localStorage.setItem = originalSetItem;
    });
  });

  describe('resetSettings', () => {
    it('should remove settings from localStorage', () => {
      const settings: SystemSettings = {
        aiSummarization: true,
        impactScoring: true,
        liabilityAcknowledged: true,
      };

      saveSettings(settings);
      expect(localStorage.getItem('policy_aggregator_system_settings')).not.toBeNull();

      resetSettings();
      expect(localStorage.getItem('policy_aggregator_system_settings')).toBeNull();
    });
  });
});

