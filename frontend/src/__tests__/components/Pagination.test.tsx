/**
 * Pagination Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Pagination from '../../components/Pagination';

describe('Pagination Component', () => {
  it('should render pagination controls', () => {
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        totalItems={100}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    expect(screen.getByText('Showing 1-20 of 100 routes')).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('should disable Previous button on first page', () => {
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        totalItems={100}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeDisabled();
  });

  it('should disable Next button on last page', () => {
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={5}
        totalPages={5}
        totalItems={100}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    const nextButton = screen.getByText('Next');
    expect(nextButton).toBeDisabled();
  });

  it('should call onPageChange when Next is clicked', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        totalItems={100}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('should call onPageChange when Previous is clicked', async () => {
    const user = userEvent.setup();
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        totalItems={100}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    const prevButton = screen.getByText('Previous');
    await user.click(prevButton);

    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('should not render pagination if only one page', () => {
    const onPageChange = vi.fn();
    
    render(
      <Pagination
        currentPage={1}
        totalPages={1}
        totalItems={10}
        pageSize={20}
        onPageChange={onPageChange}
      />
    );

    expect(screen.getByText('Showing 1-10 of 10 routes')).toBeInTheDocument();
    expect(screen.queryByText('Previous')).not.toBeInTheDocument();
    expect(screen.queryByText('Next')).not.toBeInTheDocument();
  });
});

