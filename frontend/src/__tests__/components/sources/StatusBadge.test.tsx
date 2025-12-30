/**
 * Status Badge Component Tests
 * Tests status badge rendering and color coding
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from '../../../components/sources/StatusBadge';

describe('StatusBadge', () => {
  it('should render healthy status badge', () => {
    render(<StatusBadge status="healthy" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Healthy');
    expect(badge).toHaveClass('bg-green-500');
    expect(badge).toHaveClass('text-white');
  });

  it('should render stale status badge', () => {
    render(<StatusBadge status="stale" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Stale');
    expect(badge).toHaveClass('bg-yellow-500');
    expect(badge).toHaveClass('text-black');
  });

  it('should render error status badge', () => {
    render(<StatusBadge status="error" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Error');
    expect(badge).toHaveClass('bg-red-500');
    expect(badge).toHaveClass('text-white');
  });

  it('should render never_checked status badge', () => {
    render(<StatusBadge status="never_checked" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Never Checked');
    expect(badge).toHaveClass('bg-gray-400');
    expect(badge).toHaveClass('text-white');
  });

  it('should apply custom className', () => {
    render(<StatusBadge status="healthy" className="custom-class" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('custom-class');
  });

  it('should have accessible label', () => {
    render(<StatusBadge status="healthy" />);
    
    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Source status: Healthy');
  });
});

