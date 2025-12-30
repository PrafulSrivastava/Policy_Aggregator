/**
 * Login Page Component Tests
 * Tests enhanced login module with validation, mock auth, loading, and error handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HashRouter } from 'react-router-dom';
import Login from '../pages/Login';
import { AuthProvider } from '../contexts/AuthContext';
import * as authService from '../services/auth';

// Mock the auth service
vi.mock('../services/auth', () => ({
  login: vi.fn(),
  logout: vi.fn().mockResolvedValue(undefined),
  getCurrentUser: vi.fn().mockResolvedValue(null),
}));

// Mock the API client
vi.mock('../services/api', () => ({
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

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams()],
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <HashRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </HashRouter>
);

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset environment variable
    import.meta.env.VITE_MOCK_AUTH = 'true';
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render login form with updated labels', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByLabelText(/user id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/access key/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /initialize session/i })).toBeInTheDocument();
  });

  it('should disable submit button when fields are empty', () => {
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /initialize session/i });
    expect(submitButton).toBeDisabled();
  });

  it('should enable submit button when fields are filled', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const userIdInput = screen.getByLabelText(/user id/i);
    const accessKeyInput = screen.getByLabelText(/access key/i);
    const submitButton = screen.getByRole('button', { name: /initialize session/i });

    await user.type(userIdInput, 'test@example.com');
    await user.type(accessKeyInput, 'password');

    expect(submitButton).not.toBeDisabled();
  });

  it('should show "Missing Credentials" error when User ID is empty', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const accessKeyInput = screen.getByLabelText(/access key/i);
    await user.type(accessKeyInput, 'password');

    const submitButton = screen.getByRole('button', { name: /initialize session/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/missing credentials/i)).toBeInTheDocument();
      expect(screen.getByText(/user id is required/i)).toBeInTheDocument();
    });
  });

  it('should show "Missing Credentials" error when Access Key is empty', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const userIdInput = screen.getByLabelText(/user id/i);
    await user.type(userIdInput, 'test@example.com');

    const submitButton = screen.getByRole('button', { name: /initialize session/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/missing credentials/i)).toBeInTheDocument();
      expect(screen.getByText(/access key is required/i)).toBeInTheDocument();
    });
  });

  it('should show loading spinner during login', async () => {
    vi.useFakeTimers();
    const user = userEvent.setup({ delay: null });
    
    vi.mocked(authService.login).mockImplementation(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return { success: true };
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const userIdInput = screen.getByLabelText(/user id/i);
    const accessKeyInput = screen.getByLabelText(/access key/i);
    const submitButton = screen.getByRole('button', { name: /initialize session/i });

    await user.type(userIdInput, 'admin@example.com');
    await user.type(accessKeyInput, 'password');
    await user.click(submitButton);

    // Should show loading spinner
    await waitFor(() => {
      expect(screen.getByText(/initializing session/i)).toBeInTheDocument();
    });

    // Fast-forward time
    vi.advanceTimersByTime(1500);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });

    vi.useRealTimers();
  });

  it('should show "Access Denied" error for invalid credentials', async () => {
    const user = userEvent.setup();
    vi.mocked(authService.login).mockResolvedValue({
      success: false,
      error: 'Access Denied',
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const userIdInput = screen.getByLabelText(/user id/i);
    const accessKeyInput = screen.getByLabelText(/access key/i);
    const submitButton = screen.getByRole('button', { name: /initialize session/i });

    await user.type(userIdInput, 'wrong@example.com');
    await user.type(accessKeyInput, 'wrongpassword');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
    });
  });

  it('should redirect to dashboard on successful login', async () => {
    vi.useFakeTimers();
    const user = userEvent.setup({ delay: null });
    
    vi.mocked(authService.login).mockImplementation(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      return { success: true };
    });

    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const userIdInput = screen.getByLabelText(/user id/i);
    const accessKeyInput = screen.getByLabelText(/access key/i);
    const submitButton = screen.getByRole('button', { name: /initialize session/i });

    await user.type(userIdInput, 'admin@example.com');
    await user.type(accessKeyInput, 'password');
    await user.click(submitButton);

    // Fast-forward time
    vi.advanceTimersByTime(1500);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
    });

    vi.useRealTimers();
  });

  it('should clear validation errors when user types', async () => {
    const user = userEvent.setup();
    render(
      <TestWrapper>
        <Login />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /initialize session/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/missing credentials/i)).toBeInTheDocument();
    });

    const userIdInput = screen.getByLabelText(/user id/i);
    await user.type(userIdInput, 'test@example.com');

    await waitFor(() => {
      expect(screen.queryByText(/missing credentials/i)).not.toBeInTheDocument();
    });
  });
});

