/**
 * Add Route Page Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AddRoute from '../../../pages/routes/Add';
import { createRoute } from '../../../services/routes';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the routes service
vi.mock('../../../services/routes', () => ({
  createRoute: vi.fn(),
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
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('Add Route Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the form with all fields', () => {
    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    expect(screen.getByText('Add Route')).toBeInTheDocument();
    expect(screen.getByLabelText(/origin country/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/destination country/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/visa type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create route/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty required fields', async () => {
    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: /create route/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/origin country is required/i)).toBeInTheDocument();
      expect(screen.getByText(/destination country is required/i)).toBeInTheDocument();
      expect(screen.getByText(/visa type is required/i)).toBeInTheDocument();
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });

    expect(createRoute).not.toHaveBeenCalled();
  });

  it('should validate email format', async () => {
    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.blur(emailInput);

    await waitFor(() => {
      expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument();
    });
  });

  it('should submit form with valid data', async () => {
    const mockCreatedRoute = {
      id: '123',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      email: 'user@example.com',
      is_active: true,
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(createRoute).mockResolvedValue(mockCreatedRoute);

    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    // Fill in form fields
    const originSelect = screen.getByLabelText(/origin country/i);
    const destinationSelect = screen.getByLabelText(/destination country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(originSelect, { target: { value: 'IN' } });
    fireEvent.change(destinationSelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create route/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(createRoute).toHaveBeenCalledWith({
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: 'user@example.com',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/routes', {
        state: {
          message: expect.stringContaining('created successfully'),
        },
      });
    });
  });

  it('should handle duplicate route error (409)', async () => {
    const duplicateError = new Error('This route already exists') as Error & {
      code: string;
      status: number;
    };
    duplicateError.code = 'DUPLICATE_ROUTE';
    duplicateError.status = 409;

    vi.mocked(createRoute).mockRejectedValue(duplicateError);

    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    // Fill in form fields
    const originSelect = screen.getByLabelText(/origin country/i);
    const destinationSelect = screen.getByLabelText(/destination country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(originSelect, { target: { value: 'IN' } });
    fireEvent.change(destinationSelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create route/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/this route already exists/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle validation errors from backend (400)', async () => {
    const validationError = new Error('Validation failed') as Error & {
      code: string;
      status: number;
      details?: { [key: string]: string[] };
    };
    validationError.code = 'VALIDATION_ERROR';
    validationError.status = 400;
    validationError.details = {
      email: ['Invalid email format'],
      origin_country: ['Country code must be 2 characters'],
    };

    vi.mocked(createRoute).mockRejectedValue(validationError);

    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    // Fill in form fields
    const originSelect = screen.getByLabelText(/origin country/i);
    const destinationSelect = screen.getByLabelText(/destination country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(originSelect, { target: { value: 'IN' } });
    fireEvent.change(destinationSelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create route/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
      expect(screen.getByText(/country code must be 2 characters/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show loading state during submission', async () => {
    vi.mocked(createRoute).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    // Fill in form fields
    const originSelect = screen.getByLabelText(/origin country/i);
    const destinationSelect = screen.getByLabelText(/destination country/i);
    const visaTypeSelect = screen.getByLabelText(/visa type/i);
    const emailInput = screen.getByLabelText(/email/i);

    fireEvent.change(originSelect, { target: { value: 'IN' } });
    fireEvent.change(destinationSelect, { target: { value: 'DE' } });
    fireEvent.change(visaTypeSelect, { target: { value: 'Student' } });
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create route/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/creating route/i)).toBeInTheDocument();
    });
  });

  it('should navigate to routes list on cancel', () => {
    render(
      <TestWrapper>
        <AddRoute />
      </TestWrapper>
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/routes');
  });
});

