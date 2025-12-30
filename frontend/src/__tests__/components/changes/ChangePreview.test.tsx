/**
 * Change Preview Component Tests
 * Tests change preview rendering and interaction
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ChangePreview from '../../../components/changes/ChangePreview';
import type { PolicyChange } from '../../../services/changes';

describe('ChangePreview', () => {
  const mockChange: PolicyChange = {
    id: 'change-1',
    detected_at: '2025-01-27T10:00:00Z',
    summary: 'Policy content has been updated with new requirements for student visas. The application process now requires additional documentation.',
    is_new: true,
    diff_length: 250,
    source: {
      id: 'source-1',
      name: 'Germany Student Visa Source',
      url: 'https://example.com/policy',
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
  };

  it('should render change preview with all information', () => {
    render(<ChangePreview change={mockChange} />);

    expect(screen.getByText('Germany Student Visa Source')).toBeInTheDocument();
    expect(screen.getByText(/Policy content has been updated/)).toBeInTheDocument();
    expect(screen.getByText('New')).toBeInTheDocument();
  });

  it('should truncate long summary text', () => {
    const longSummaryChange: PolicyChange = {
      ...mockChange,
      summary: 'A'.repeat(200),
    };

    render(<ChangePreview change={longSummaryChange} />);

    // Find the preview text by checking for truncated content
    const previewText = screen.getByText(/A{150}\.\.\./);
    expect(previewText).toBeInTheDocument();
  });

  it('should call onAnalyzeClick when Analyze Diff button is clicked', () => {
    const mockOnAnalyzeClick = vi.fn();
    render(<ChangePreview change={mockChange} onAnalyzeClick={mockOnAnalyzeClick} />);

    const analyzeButton = screen.getByText('Analyze Diff');
    fireEvent.click(analyzeButton);

    expect(mockOnAnalyzeClick).toHaveBeenCalledTimes(1);
  });

  it('should not render Analyze Diff button when onAnalyzeClick is not provided', () => {
    render(<ChangePreview change={mockChange} />);

    expect(screen.queryByText('Analyze Diff')).not.toBeInTheDocument();
  });

  it('should format timestamp correctly', () => {
    render(<ChangePreview change={mockChange} />);

    // Check that timestamp is rendered (format may vary by locale)
    const timestampElement = screen.getByText(/2025/);
    expect(timestampElement).toBeInTheDocument();
  });

  it('should display source name', () => {
    render(<ChangePreview change={mockChange} />);

    expect(screen.getByText('Germany Student Visa Source')).toBeInTheDocument();
  });

  it('should not display New badge when is_new is false', () => {
    const notNewChange: PolicyChange = {
      ...mockChange,
      is_new: false,
    };

    render(<ChangePreview change={notNewChange} />);

    expect(screen.queryByText('New')).not.toBeInTheDocument();
  });
});

