/**
 * Recent Signals Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import RecentSignals from '../../components/RecentSignals';
import type { ChangeItem } from '../../services/dashboard';

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <HashRouter>
    {children}
  </HashRouter>
);

describe('RecentSignals Component', () => {
  const mockChanges: ChangeItem[] = [
    {
      id: '1',
      detected_at: '2025-01-27T10:00:00Z',
      source: {
        id: 'source-1',
        name: 'Germany Student Visa',
        country: 'DE',
        visa_type: 'Student',
      },
      route: {
        id: 'route-1',
        origin_country: 'IN',
        destination_country: 'DE',
        visa_type: 'Student',
        display: 'IN → DE, Student',
      },
      summary: 'Content changed',
      is_new: true,
      diff_length: 150,
    },
  ];

  it('should render loading state', () => {
    render(
      <TestWrapper>
        <RecentSignals changes={[]} loading={true} />
      </TestWrapper>
    );

    expect(screen.getByText('Recent Signals')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should render error state', () => {
    render(
      <TestWrapper>
        <RecentSignals changes={[]} error="Failed to load" />
      </TestWrapper>
    );

    expect(screen.getByText('Recent Signals')).toBeInTheDocument();
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('should render empty state', () => {
    render(
      <TestWrapper>
        <RecentSignals changes={[]} />
      </TestWrapper>
    );

    expect(screen.getByText('Recent Signals')).toBeInTheDocument();
    expect(screen.getByText(/no recent changes detected/i)).toBeInTheDocument();
    expect(screen.getByText('View Full History')).toBeInTheDocument();
  });

  it('should render recent changes', () => {
    render(
      <TestWrapper>
        <RecentSignals changes={mockChanges} />
      </TestWrapper>
    );

    expect(screen.getByText('Recent Signals')).toBeInTheDocument();
    expect(screen.getByText('Germany Student Visa')).toBeInTheDocument();
    expect(screen.getByText('IN → DE, Student')).toBeInTheDocument();
    expect(screen.getByText('Content changed')).toBeInTheDocument();
    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('should have link to full history', () => {
    render(
      <TestWrapper>
        <RecentSignals changes={mockChanges} />
      </TestWrapper>
    );

    const link = screen.getByText('View Full History →');
    expect(link).toBeInTheDocument();
    expect(link.closest('a')).toHaveAttribute('href', '#/changes');
  });
});

