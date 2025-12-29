/**
 * Routes Page Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Routes from '../../pages/Routes';
import { getRoutes, type PaginatedRoutesResponse } from '../../services/routes';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the routes service
vi.mock('../../services/routes', () => ({
  getRoutes: vi.fn(),
}));

// Mock the auth service
vi.mock('../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
  logout: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API client
vi.mock('../../services/api', () => ({
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

describe('Routes Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    vi.mocked(getRoutes).mockImplementation(() => new Promise<PaginatedRoutesResponse>(() => {})); // Never resolves
    
    render(
      <TestWrapper>
        <Routes />
      </TestWrapper>
    );

    expect(screen.getByText('Loading routes...')).toBeInTheDocument();
  });

  it('should render routes list when data is loaded', async () => {
    const mockRoutes = {
      items: [
        {
          id: '123',
          origin_country: 'IN',
          destination_country: 'DE',
          visa_type: 'Student',
          email: 'user@example.com',
          is_active: true,
          created_at: '2025-01-27T10:00:00Z',
          updated_at: '2025-01-27T10:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    };

    vi.mocked(getRoutes).mockResolvedValue(mockRoutes);

    render(
      <TestWrapper>
        <Routes />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('IN → DE')).toBeInTheDocument();
      expect(screen.getByText('Student')).toBeInTheDocument();
      expect(screen.getByText('user@example.com')).toBeInTheDocument();
    });
  });

  it('should render empty state when no routes', async () => {
    const mockRoutes = {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    };

    vi.mocked(getRoutes).mockResolvedValue(mockRoutes);

    render(
      <TestWrapper>
        <Routes />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('No routes configured yet')).toBeInTheDocument();
      expect(screen.getByText('Add Your First Route')).toBeInTheDocument();
    });
  });

  it('should render error state when API call fails', async () => {
    vi.mocked(getRoutes).mockRejectedValue(new Error('API Error'));

    render(
      <TestWrapper>
        <Routes />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });
});

