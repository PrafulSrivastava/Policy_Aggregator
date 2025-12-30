/**
 * Quick Actions Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HashRouter } from 'react-router-dom';
import QuickActions from '../../components/QuickActions';

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <HashRouter>
    {children}
  </HashRouter>
);

describe('QuickActions Component', () => {
  it('should render loading state', () => {
    render(
      <TestWrapper>
        <QuickActions totalRoutes={0} activeSources={0} loading={true} />
      </TestWrapper>
    );

    expect(screen.getAllByText('Loading...')).toHaveLength(2);
  });

  it('should render route index card', () => {
    render(
      <TestWrapper>
        <QuickActions totalRoutes={5} activeSources={8} />
      </TestWrapper>
    );

    expect(screen.getByText('Route Index')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Total Routes')).toBeInTheDocument();
    expect(screen.getByText('Route Configuration →')).toBeInTheDocument();
  });

  it('should render source nodes card', () => {
    render(
      <TestWrapper>
        <QuickActions totalRoutes={5} activeSources={8} />
      </TestWrapper>
    );

    expect(screen.getByText('Source Nodes')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('Active Sources')).toBeInTheDocument();
    expect(screen.getByText('Source Management →')).toBeInTheDocument();
  });

  it('should have links to routes and sources', () => {
    render(
      <TestWrapper>
        <QuickActions totalRoutes={5} activeSources={8} />
      </TestWrapper>
    );

    const routeLink = screen.getByText('Route Index').closest('a');
    const sourceLink = screen.getByText('Source Nodes').closest('a');

    expect(routeLink).toHaveAttribute('href', '#/routes');
    expect(sourceLink).toHaveAttribute('href', '#/sources');
  });
});

