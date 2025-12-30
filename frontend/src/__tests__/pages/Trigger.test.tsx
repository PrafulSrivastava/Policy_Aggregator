/**
 * Manual Trigger Diagnostics Page Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Trigger from '../../pages/Trigger';
import * as sourcesService from '../../services/sources';

// Mock the sources service
vi.mock('../../services/sources', () => ({
  getSources: vi.fn(),
  triggerSourceFetch: vi.fn(),
}));

// Mock the auth service
vi.mock('../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
  logout: vi.fn().mockResolvedValue(undefined),
}));

// Mock the API client
vi.mock('../../services/api', () => ({
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

describe('Trigger Page', () => {
  const mockSources = [
    {
      id: 'source-1',
      name: 'Germany Student Visa',
      country: 'DE',
      visa_type: 'Student',
      url: 'https://example.com',
      fetch_type: 'html' as const,
      check_frequency: 'daily' as const,
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    },
    {
      id: 'source-2',
      name: 'UK Work Visa',
      country: 'UK',
      visa_type: 'Work',
      url: 'https://example.com/uk',
      fetch_type: 'html' as const,
      check_frequency: 'daily' as const,
      is_active: true,
      last_checked_at: null,
      last_change_detected_at: null,
      metadata: {},
      created_at: '2025-01-27T10:00:00Z',
      updated_at: '2025-01-27T10:00:00Z',
    },
  ];

  const mockTriggerResponse = {
    success: true,
    sourceId: 'source-1',
    changeDetected: true,
    policyVersionId: 'version-1',
    policyChangeId: 'change-1',
    error: null,
    fetchedAt: '2025-01-27T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('should render page with header', async () => {
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Manual Trigger Diagnostics')).toBeInTheDocument();
    });
  });

  it('should load sources and display in dropdown', async () => {
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(sourcesService.getSources).toHaveBeenCalledWith(1, 100);
    });

    const select = screen.getByLabelText(/target node/i);
    expect(select).toBeInTheDocument();
  });

  it('should trigger fetch when button is clicked', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    vi.mocked(sourcesService.triggerSourceFetch).mockResolvedValue(mockTriggerResponse);

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/target node/i)).toBeInTheDocument();
    });

    // Select a source
    const select = screen.getByLabelText(/target node/i);
    await user.selectOptions(select, 'source-1');

    // Click trigger button
    const triggerButton = screen.getByText('Initialize Fetch');
    await user.click(triggerButton);

    // Wait for API call
    await waitFor(() => {
      expect(sourcesService.triggerSourceFetch).toHaveBeenCalledWith('source-1');
    });
  });

  it('should show error if no source is selected', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Initialize Fetch')).toBeInTheDocument();
    });

    const triggerButton = screen.getByText('Initialize Fetch');
    await user.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText(/please select a source/i)).toBeInTheDocument();
    });
  });

  it('should display terminal output during fetch', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    vi.mocked(sourcesService.triggerSourceFetch).mockImplementation(
      () => new Promise((resolve) => {
        setTimeout(() => resolve(mockTriggerResponse), 2000);
      })
    );

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/target node/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/target node/i);
    await user.selectOptions(select, 'source-1');

    const triggerButton = screen.getByText('Initialize Fetch');
    await user.click(triggerButton);

    // Advance timers to trigger network simulation
    vi.advanceTimersByTime(500);

    await waitFor(() => {
      expect(screen.getByText(/initializing fetch operation/i)).toBeInTheDocument();
    });
  });

  it('should handle fetch errors', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    vi.mocked(sourcesService.triggerSourceFetch).mockRejectedValue(
      new Error('Network error')
    );

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/target node/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/target node/i);
    await user.selectOptions(select, 'source-1');

    const triggerButton = screen.getByText('Initialize Fetch');
    await user.click(triggerButton);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('should display result visualization after successful fetch', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    
    vi.mocked(sourcesService.getSources).mockResolvedValue({
      items: mockSources,
      total: 2,
      page: 1,
      page_size: 100,
    });

    vi.mocked(sourcesService.triggerSourceFetch).mockResolvedValue(mockTriggerResponse);

    render(
      <TestWrapper>
        <Trigger />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/target node/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/target node/i);
    await user.selectOptions(select, 'source-1');

    const triggerButton = screen.getByText('Initialize Fetch');
    await user.click(triggerButton);

    // Advance timers to complete fetch
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(screen.getByText('Result Visualization')).toBeInTheDocument();
      expect(screen.getByText('Yes')).toBeInTheDocument(); // Change detected
    });
  });
});

