/**
 * Add Source Page Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AddSource from '../../../pages/sources/Add';
import { createSource } from '../../../services/sources';
import { AuthProvider } from '../../../contexts/AuthContext';
import type { RouteSubscription } from '../../../services/routes';

// Mock the sources service
vi.mock('../../../services/sources', () => ({
  createSource: vi.fn(),
  addSourceToRoute: vi.fn(),
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

// Mock react-router-dom
const mockNavigate = vi.fn();
const mockUseLocation = vi.fn(() => ({ state: null as unknown, pathname: '/sources/new', search: '', hash: '', key: 'test' }));
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockUseLocation(),
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Add Source Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the form with all fields', () => {
    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    expect(screen.getByText('Add Source')).toBeInTheDocument();
    expect(screen.getByLabelText(/country/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/visa type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/source url/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/source name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/fetch type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/check frequency/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create source/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty required fields', async () => {
    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /create source/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/country is required/i)).toBeInTheDocument();
      expect(screen.getByText(/visa type is required/i)).toBeInTheDocument();
      expect(screen.getByText(/url is required/i)).toBeInTheDocument();
      expect(screen.getByText(/source name is required/i)).toBeInTheDocument();
    });

    expect(createSource).not.toHaveBeenCalled();
  });

  it('should validate URL format', async () => {
    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    const urlInput = screen.getByLabelText(/source url/i);
    fireEvent.change(urlInput, { target: { value: 'invalid-url' } });
    fireEvent.blur(urlInput);

    const submitButton = screen.getByRole('button', { name: /create source/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid url/i)).toBeInTheDocument();
    });
  });

  it('should submit form with valid data', async () => {
    const mockCreatedSource = {
      id: '123',
      country: 'DE',
      visa_type: 'Student',
      url: 'https://example.com/policy',
      name: 'Test Source',
      fetch_type: 'html' as const,
      check_frequency: 'daily' as const,
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(createSource).mockResolvedValue(mockCreatedSource);

    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    // Fill in form fields
    const countrySelect = screen.getByLabelText(/country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const urlInput = screen.getByLabelText(/source url/i);
    const nameInput = screen.getByLabelText(/source name/i);
    const htmlRadio = screen.getByLabelText(/html/i);
    const frequencySelect = screen.getByLabelText(/check frequency/i);

    fireEvent.change(countrySelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(urlInput, { target: { value: 'https://example.com/policy' } });
    fireEvent.change(nameInput, { target: { value: 'Test Source' } });
    fireEvent.click(htmlRadio);
    fireEvent.change(frequencySelect, { target: { value: 'daily' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create source/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(createSource).toHaveBeenCalledWith({
        country: 'DE',
        visaType: 'Student',
        url: 'https://example.com/policy',
        name: 'Test Source',
        fetchType: 'html',
        checkFrequency: 'daily',
        isActive: true,
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/sources', {
        state: {
          message: expect.stringContaining('created successfully'),
        },
      });
    });
  });

  it('should handle duplicate source error (409)', async () => {
    const duplicateError = new Error('This source already exists') as Error & {
      code: string;
      status: number;
    };
    duplicateError.code = 'DUPLICATE_SOURCE';
    duplicateError.status = 409;

    vi.mocked(createSource).mockRejectedValue(duplicateError);

    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    // Fill in form fields
    const countrySelect = screen.getByLabelText(/country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const urlInput = screen.getByLabelText(/source url/i);
    const nameInput = screen.getByLabelText(/source name/i);
    const htmlRadio = screen.getByLabelText(/html/i);
    const frequencySelect = screen.getByLabelText(/check frequency/i);

    fireEvent.change(countrySelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(urlInput, { target: { value: 'https://example.com/policy' } });
    fireEvent.change(nameInput, { target: { value: 'Test Source' } });
    fireEvent.click(htmlRadio);
    fireEvent.change(frequencySelect, { target: { value: 'daily' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create source/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/this source already exists/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should pre-fill fields when route context is provided', () => {
    const mockRoute: RouteSubscription = {
      id: 'route-123',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      email: 'test@example.com',
      is_active: true,
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    // Mock useLocation to return route context
    mockUseLocation.mockReturnValue({
      state: { route: mockRoute },
      pathname: '/sources/new',
      search: '',
      hash: '',
      key: 'test',
    });

    render(
      <TestWrapper>
        <AddSource />
      </TestWrapper>
    );

    expect(screen.getByText(/adding source for route/i)).toBeInTheDocument();
    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement;
    const visaTypeSelect = screen.getByLabelText(/visa type/i) as HTMLSelectElement;
    
    // Fields should be pre-filled and disabled
    expect(countrySelect.value).toBe('DE');
    expect(visaTypeSelect.value).toBe('Student');
  });
});

