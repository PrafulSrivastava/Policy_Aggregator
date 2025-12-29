/**
 * Empty State Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import EmptyState from '../../components/EmptyState';

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('EmptyState Component', () => {
  it('should render title', () => {
    render(
      <TestWrapper>
        <EmptyState title="No items" />
      </TestWrapper>
    );
    expect(screen.getByText('No items')).toBeInTheDocument();
  });

  it('should render message when provided', () => {
    render(
      <TestWrapper>
        <EmptyState title="No items" message="Get started by adding an item" />
      </TestWrapper>
    );
    expect(screen.getByText('Get started by adding an item')).toBeInTheDocument();
  });

  it('should render link button when actionHref is provided', () => {
    render(
      <TestWrapper>
        <EmptyState
          title="No items"
          actionLabel="Add Item"
          actionHref="/add"
        />
      </TestWrapper>
    );
    const link = screen.getByText('Add Item');
    expect(link).toBeInTheDocument();
    expect(link.closest('a')).toHaveAttribute('href', '/add');
  });

  it('should render button when onAction is provided', async () => {
    const onAction = vi.fn();
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <EmptyState
          title="No items"
          actionLabel="Add Item"
          onAction={onAction}
        />
      </TestWrapper>
    );
    
    const button = screen.getByText('Add Item');
    expect(button).toBeInTheDocument();
    
    await user.click(button);
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});

