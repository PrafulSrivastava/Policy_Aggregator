/**
 * Notification Settings Page Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Notifications from '../../../pages/settings/Notifications';
import { getNotificationSettings, updateNotificationSettings } from '../../../services/notifications';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the notifications service
vi.mock('../../../services/notifications', () => ({
  getNotificationSettings: vi.fn(),
  updateNotificationSettings: vi.fn(),
}));

// Mock the auth service
vi.mock('../../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
  logout: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API client
vi.mock('../../../services/api', () => ({
  getToken: vi.fn().mockReturnValue('test-token'),
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
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Notification Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the settings form', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    });

    expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save settings/i })).toBeInTheDocument();
  });

  it('should load and display current settings', async () => {
    const mockSettings = {
      enabled: true,
      frequency: 'daily',
      email: 'user@example.com',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enabled/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/daily digest/i)).toBeInTheDocument();
  });

  it('should show loading state while fetching settings', () => {
    vi.mocked(getNotificationSettings).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    expect(screen.getByText(/loading notification settings/i)).toBeInTheDocument();
  });

  it('should handle 501 Not Implemented error gracefully', async () => {
    const notImplementedError = new Error('Notification settings service is not available') as Error & {
      code: string;
      status: number;
    };
    notImplementedError.code = 'NOT_IMPLEMENTED';
    notImplementedError.status = 501;

    vi.mocked(getNotificationSettings).mockRejectedValue(notImplementedError);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/notification settings service is not available/i)).toBeInTheDocument();
    });
  });

  it('should validate email when notifications are enabled', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Submit without email
    const submitButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/email is required when notifications are enabled/i)).toBeInTheDocument();
    });
  });

  it('should validate email format', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Enter invalid email
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    // Submit
    const submitButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/valid email address/i)).toBeInTheDocument();
    });
  });

  it('should save settings successfully', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    const updatedSettings = {
      enabled: true,
      frequency: 'daily',
      email: 'user@example.com',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);
    vi.mocked(updateNotificationSettings).mockResolvedValue(updatedSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Fill in email
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Select frequency
    const frequencySelect = screen.getByLabelText(/notification frequency/i);
    fireEvent.change(frequencySelect, { target: { value: 'daily' } });

    // Submit
    const submitButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(updateNotificationSettings).toHaveBeenCalledWith({
        enabled: true,
        frequency: 'daily',
        email: 'user@example.com',
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/notification settings saved successfully/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during save', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);
    vi.mocked(updateNotificationSettings).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Fill in email
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit
    const submitButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });
  });

  it('should handle save error', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);
    vi.mocked(updateNotificationSettings).mockRejectedValue(new Error('Failed to save'));

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Fill in email
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit
    const submitButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to save/i)).toBeInTheDocument();
    });
  });

  it('should show email and frequency fields only when enabled', async () => {
    const mockSettings = {
      enabled: false,
      frequency: 'immediate',
      email: '',
    };

    vi.mocked(getNotificationSettings).mockResolvedValue(mockSettings);

    render(
      <TestWrapper>
        <Notifications />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/enable email notifications/i)).toBeInTheDocument();
    });

    // Email and frequency should not be visible initially
    expect(screen.queryByLabelText(/email address/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/notification frequency/i)).not.toBeInTheDocument();

    // Enable notifications
    const toggle = screen.getByRole('checkbox');
    fireEvent.click(toggle);

    // Email and frequency should now be visible
    await waitFor(() => {
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/notification frequency/i)).toBeInTheDocument();
    });
  });
});

