/**
 * Source Modal Component Tests
 * Tests source modal for creating and editing sources
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SourceModal from '../../../components/sources/SourceModal';
import * as sourcesService from '../../../services/sources';

// Mock the sources service
vi.mock('../../../services/sources', () => ({
  createSource: vi.fn(),
  updateSource: vi.fn(),
}));

// Mock the form components
vi.mock('../../../components/forms/Select', () => ({
  default: ({ value, onChange, options, label, id, ...props }: any) => (
    <div>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium mb-2 uppercase tracking-widest">
          {label}
        </label>
      )}
      <select id={id} value={value} onChange={onChange} {...props}>
        {options?.map((opt: any) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  ),
}));

vi.mock('../../../components/forms/Input', () => ({
  default: ({ value, onChange, label, id, ...props }: any) => (
    <div>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium mb-2 uppercase tracking-widest">
          {label}
        </label>
      )}
      <input id={id} value={value} onChange={onChange} {...props} />
    </div>
  ),
}));

vi.mock('../../../components/forms/Radio', () => ({
  default: ({ value, onChange, options, name, label, id, ...props }: any) => (
    <div {...props}>
      {label && (
        <label htmlFor={id || name} className="block text-sm font-medium mb-2 uppercase tracking-widest">
          {label}
        </label>
      )}
      <div role="radiogroup" aria-labelledby={id || name}>
        {options?.map((opt: any) => (
          <label key={opt.value} htmlFor={`${name}-${opt.value}`}>
            <input
              id={`${name}-${opt.value}`}
              type="radio"
              name={name}
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
              aria-labelledby={label ? id || name : undefined}
            />
            {opt.label}
          </label>
        ))}
      </div>
    </div>
  ),
}));

describe('SourceModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when closed', () => {
    render(
      <SourceModal
        isOpen={false}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.queryByText('Add Node')).not.toBeInTheDocument();
  });

  it('should render create mode when open without source', () => {
    render(
      <SourceModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    expect(screen.getByText('Add Node')).toBeInTheDocument();
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/region/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/endpoint url/i)).toBeInTheDocument();
    expect(screen.getByText(/fetch method/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/frequency/i)).toBeInTheDocument();
    expect(screen.getByText('Create')).toBeInTheDocument();
  });

  it('should render edit mode when open with source', () => {
    const mockSource = {
      id: 'source-1',
      name: 'Test Source',
      country: 'DE',
      visa_type: 'Student',
      url: 'https://example.com/policy',
      fetch_type: 'html' as const,
      check_frequency: 'daily' as const,
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    render(
      <SourceModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        source={mockSource}
      />
    );

    expect(screen.getByText('Edit Source')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Source')).toBeInTheDocument();
    expect(screen.getByDisplayValue('https://example.com/policy')).toBeInTheDocument();
    expect(screen.getByText('Update')).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    const user = userEvent.setup();
    render(
      <SourceModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    const submitButton = screen.getByText('Create');
    await user.click(submitButton);

    // Form should not submit without required fields
    expect(sourcesService.createSource).not.toHaveBeenCalled();
  });

  it('should call createSource when submitting valid form in create mode', async () => {
    const user = userEvent.setup();
    vi.mocked(sourcesService.createSource).mockResolvedValue({
      id: 'new-source',
      name: 'New Source',
      country: 'DE',
      visa_type: 'Student',
      url: 'https://example.com/policy',
      fetch_type: 'html',
      check_frequency: 'daily',
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    });

    render(
      <SourceModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />
    );

    // Fill in form
    await user.type(screen.getByLabelText(/name/i), 'New Source');
    await user.selectOptions(screen.getByLabelText(/region/i), 'DE');
    await user.selectOptions(screen.getByLabelText(/type/i), 'Student');
    await user.type(screen.getByLabelText(/endpoint url/i), 'https://example.com/policy');

    // Submit form
    const submitButton = screen.getByText('Create');
    await user.click(submitButton);

    await waitFor(() => {
      expect(sourcesService.createSource).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'New Source',
          country: 'DE',
          visaType: 'Student',
          url: 'https://example.com/policy',
          fetchType: 'html',
          checkFrequency: 'daily',
          isActive: true,
        })
      );
    });

    expect(mockOnSuccess).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should call updateSource when submitting valid form in edit mode', async () => {
    const user = userEvent.setup();
    const mockSource = {
      id: 'source-1',
      name: 'Test Source',
      country: 'DE',
      visa_type: 'Student',
      url: 'https://example.com/policy',
      fetch_type: 'html' as const,
      check_frequency: 'daily' as const,
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    };

    vi.mocked(sourcesService.updateSource).mockResolvedValue({
      ...mockSource,
      name: 'Updated Source',
    });

    render(
      <SourceModal
        isOpen={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        source={mockSource}
      />
    );

    // Update name
    const nameInput = screen.getByLabelText(/name/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Source');

    // Submit form
    const submitButton = screen.getByText('Update');
    await user.click(submitButton);

    await waitFor(() => {
      expect(sourcesService.updateSource).toHaveBeenCalledWith(
        'source-1',
        expect.objectContaining({
          name: 'Updated Source',
        })
      );
    });

    expect(mockOnSuccess).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });
});

