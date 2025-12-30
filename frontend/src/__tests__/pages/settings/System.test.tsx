/**
 * System Settings Page Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import System from '../../../pages/settings/System';
import * as settingsService from '../../../services/settings';

// Mock the settings service
vi.mock('../../../services/settings', () => ({
  getSettings: vi.fn(),
  saveSettings: vi.fn(),
}));

// Mock the auth service
vi.mock('../../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
  logout: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API client
vi.mock('../../../services/api', () => ({
  getToken: vi.fn().mockReturnValue(null),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('System Settings Page', () => {
  const mockSettings = {
    aiSummarization: true,
    impactScoring: true,
    liabilityAcknowledged: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('should render page with header', async () => {
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('System Settings')).toBeInTheDocument();
    });
  });

  it('should load and display current settings', async () => {
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Feature Toggles')).toBeInTheDocument();
      expect(screen.getByText('Compliance')).toBeInTheDocument();
    });

    const aiToggle = screen.getByRole('switch', { name: /ai summarization/i });
    expect(aiToggle).toHaveAttribute('aria-checked', 'true');
  });

  it('should update toggle state when toggled', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('switch', { name: /ai summarization/i })).toBeInTheDocument();
    });

    const aiToggle = screen.getByRole('switch', { name: /ai summarization/i });
    await user.click(aiToggle);

    await waitFor(() => {
      expect(aiToggle).toHaveAttribute('aria-checked', 'false');
    });
  });

  it('should require liability acknowledgment before saving', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Commit Changes')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Commit Changes');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/you must acknowledge the liability protocol/i)).toBeInTheDocument();
    });

    expect(settingsService.saveSettings).not.toHaveBeenCalled();
  });

  it('should save settings when liability is acknowledged', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);
    vi.mocked(settingsService.saveSettings).mockImplementation(() => {});

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('I Acknowledge')).toBeInTheDocument();
    });

    // Check the liability acknowledgment checkbox
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    // Submit form
    const submitButton = screen.getByText('Commit Changes');
    await user.click(submitButton);

    // Advance timers to complete save
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(settingsService.saveSettings).toHaveBeenCalled();
      expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();
    });
  });

  it('should load settings on mount', async () => {
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(settingsService.getSettings).toHaveBeenCalled();
      expect(screen.getByText('System Settings')).toBeInTheDocument();
    });
  });

  it('should display error message if settings fail to load', async () => {
    vi.mocked(settingsService.getSettings).mockImplementation(() => {
      throw new Error('Failed to load settings');
    });

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to load settings/i)).toBeInTheDocument();
    });
  });

  it('should display error message if save fails', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);
    vi.mocked(settingsService.saveSettings).mockImplementation(() => {
      throw new Error('Failed to save');
    });

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('I Acknowledge')).toBeInTheDocument();
    });

    // Check the liability acknowledgment checkbox
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    // Submit form
    const submitButton = screen.getByText('Commit Changes');
    await user.click(submitButton);

    // Advance timers to complete save
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(screen.getByText(/failed to save/i)).toBeInTheDocument();
    });
  });

  it('should disable submit button when liability is not acknowledged', async () => {
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      const submitButton = screen.getByText('Commit Changes');
      expect(submitButton).toBeDisabled();
    });
  });

  it('should show success message after successful save', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    vi.mocked(settingsService.getSettings).mockReturnValue(mockSettings);
    vi.mocked(settingsService.saveSettings).mockImplementation(() => {});

    render(
      <TestWrapper>
        <System />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('I Acknowledge')).toBeInTheDocument();
    });

    // Check the liability acknowledgment checkbox
    const checkbox = screen.getByRole('checkbox');
    await user.click(checkbox);

    // Submit form
    const submitButton = screen.getByText('Commit Changes');
    await user.click(submitButton);

    // Advance timers to complete save
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();
    });

    // Advance timers to clear success message
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(screen.queryByText('Settings saved successfully')).not.toBeInTheDocument();
    });
  });
});

