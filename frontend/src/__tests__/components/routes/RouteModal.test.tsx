/**
 * Route Modal Component Tests
 * Tests route modal for creating and editing routes
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RouteModal from '../../../components/routes/RouteModal';
import * as routesService from '../../../services/routes';

// Mock the routes service
vi.mock('../../../services/routes', () => ({
  createRoute: vi.fn(),
  updateRoute: vi.fn(),
}));

// Mock the forms components
vi.mock('../../../components/forms/Select', () => ({
  default: ({ children, value, onChange, error, ...props }: any) => (
    <select value={value} onChange={onChange} {...props}>
      {children}
    </select>
  ),
}));

describe('RouteModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when closed', () => {
    render(
      <RouteModal
        isOpen={false}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.queryByText('Initialize Route')).not.toBeInTheDocument();
  });

  it('should render create mode when open without route', () => {
    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.getByText('Initialize Route')).toBeInTheDocument();
    expect(screen.getByLabelText(/origin node/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/destination node/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/visa classification/i)).toBeInTheDocument();
    expect(screen.getByText('Confirm Sequence')).toBeInTheDocument();
  });

  it('should render edit mode when open with route', () => {
    const mockRoute = {
      id: 'route-1',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      email: 'test@example.com',
      is_active: true,
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        route={mockRoute}
      />
    );

    expect(screen.getByText('Edit Route')).toBeInTheDocument();
    expect(screen.getByDisplayValue('IN')).toBeInTheDocument();
    expect(screen.getByDisplayValue('DE')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Student')).toBeInTheDocument();
  });

  it('should validate form and show errors', async () => {
    const user = userEvent.setup();
    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const submitButton = screen.getByText('Confirm Sequence');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/origin node is required/i)).toBeInTheDocument();
      expect(screen.getByText(/destination node is required/i)).toBeInTheDocument();
      expect(screen.getByText(/visa classification is required/i)).toBeInTheDocument();
    });

    expect(routesService.createRoute).not.toHaveBeenCalled();
  });

  it('should create route on valid form submission', async () => {
    const user = userEvent.setup();
    vi.mocked(routesService.createRoute).mockResolvedValue({
      id: 'new-route',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      email: 'test@example.com',
      is_active: true,
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    });

    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill form
    const originSelect = screen.getByLabelText(/origin node/i);
    const destinationSelect = screen.getByLabelText(/destination node/i);
    const visaSelect = screen.getByLabelText(/visa classification/i);

    await user.selectOptions(originSelect, 'IN');
    await user.selectOptions(destinationSelect, 'DE');
    await user.selectOptions(visaSelect, 'Student');

    // Submit
    const submitButton = screen.getByText('Confirm Sequence');
    await user.click(submitButton);

    await waitFor(() => {
      expect(routesService.createRoute).toHaveBeenCalledWith({
        originCountry: 'IN',
        destinationCountry: 'DE',
        visaType: 'Student',
        email: '',
      });
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('should update route on valid form submission in edit mode', async () => {
    const user = userEvent.setup();
    const mockRoute = {
      id: 'route-1',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      email: 'test@example.com',
      is_active: true,
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(routesService.updateRoute).mockResolvedValue({
      ...mockRoute,
      destination_country: 'FR',
    });

    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        route={mockRoute}
      />
    );

    // Change destination
    const destinationSelect = screen.getByLabelText(/destination node/i);
    await user.selectOptions(destinationSelect, 'FR');

    // Submit
    const submitButton = screen.getByText('Confirm Sequence');
    await user.click(submitButton);

    await waitFor(() => {
      expect(routesService.updateRoute).toHaveBeenCalledWith('route-1', {
        originCountry: 'IN',
        destinationCountry: 'FR',
        visaType: 'Student',
        email: 'test@example.com',
      });
      expect(mockOnSuccess).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('should show error message on API failure', async () => {
    const user = userEvent.setup();
    vi.mocked(routesService.createRoute).mockRejectedValue(new Error('API Error'));

    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill form
    const originSelect = screen.getByLabelText(/origin node/i);
    const destinationSelect = screen.getByLabelText(/destination node/i);
    const visaSelect = screen.getByLabelText(/visa classification/i);

    await user.selectOptions(originSelect, 'IN');
    await user.selectOptions(destinationSelect, 'DE');
    await user.selectOptions(visaSelect, 'Student');

    // Submit
    const submitButton = screen.getByText('Confirm Sequence');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/api error/i)).toBeInTheDocument();
    });

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should close modal when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should clear errors when user types', async () => {
    const user = userEvent.setup();
    render(
      <RouteModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Submit empty form to trigger errors
    const submitButton = screen.getByText('Confirm Sequence');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/origin node is required/i)).toBeInTheDocument();
    });

    // Select origin to clear error
    const originSelect = screen.getByLabelText(/origin node/i);
    await user.selectOptions(originSelect, 'IN');

    await waitFor(() => {
      expect(screen.queryByText(/origin node is required/i)).not.toBeInTheDocument();
    });
  });
});

