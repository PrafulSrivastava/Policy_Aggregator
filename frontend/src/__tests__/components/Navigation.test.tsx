/**
 * Navigation Component Tests
 * Tests responsive navigation, hamburger menu, and active route highlighting
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import Navigation from '../../components/Navigation';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the auth service
vi.mock('../../services/auth', () => ({
  getCurrentUser: vi.fn().mockResolvedValue({ id: '1', username: 'testuser', is_active: true }),
  logout: vi.fn().mockResolvedValue(undefined),
  login: vi.fn().mockResolvedValue({ success: true }),
}));

// Mock the API client
vi.mock('../../services/api', () => ({
  getToken: vi.fn().mockReturnValue('mock-token'),
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
  <HashRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </HashRouter>
);

describe('Navigation', () => {
  beforeEach(() => {
    // Reset window location
    window.location.hash = '';
  });

  it('should render navigation links', () => {
    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    expect(screen.getByText('Policy Aggregator')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Routes')).toBeInTheDocument();
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Changes')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('should show hamburger menu button on mobile', () => {
    // Mock window.innerWidth for mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    const hamburgerButton = screen.getByLabelText('Toggle menu');
    expect(hamburgerButton).toBeInTheDocument();
  });

  it('should toggle mobile menu when hamburger is clicked', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    const hamburgerButton = screen.getByLabelText('Toggle menu');
    
    // Menu should be closed initially
    expect(screen.queryByText('Menu')).not.toBeInTheDocument();

    // Click to open
    fireEvent.click(hamburgerButton);
    
    // Menu should be open
    expect(screen.getByText('Menu')).toBeInTheDocument();
    
    // Click to close
    fireEvent.click(hamburgerButton);
    
    // Menu should be closed
    expect(screen.queryByText('Menu')).not.toBeInTheDocument();
  });

  it('should close mobile menu when a link is clicked', () => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    const hamburgerButton = screen.getByLabelText('Toggle menu');
    fireEvent.click(hamburgerButton);
    
    // Menu should be open
    expect(screen.getByText('Menu')).toBeInTheDocument();
    
    // Click a link
    const routesLink = screen.getAllByText('Routes')[0];
    fireEvent.click(routesLink);
    
    // Menu should be closed
    expect(screen.queryByText('Menu')).not.toBeInTheDocument();
  });

  it('should display user username when authenticated', async () => {
    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    // Wait for auth to complete
    await vi.waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });
  });

  it('should have logout button', () => {
    render(
      <TestWrapper>
        <Navigation />
      </TestWrapper>
    );

    expect(screen.getByText('Logout')).toBeInTheDocument();
  });
});

