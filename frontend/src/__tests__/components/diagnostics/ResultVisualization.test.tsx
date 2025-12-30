/**
 * Result Visualization Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResultVisualization from '../../../components/diagnostics/ResultVisualization';
import { type TriggerSourceResponse } from '../../../services/sources';

describe('ResultVisualization Component', () => {
  const mockResult: TriggerSourceResponse = {
    success: true,
    sourceId: 'source-1',
    changeDetected: true,
    policyVersionId: 'version-1',
    policyChangeId: 'change-1',
    error: null,
    fetchedAt: '2025-01-27T10:00:00Z',
  };

  it('should render result visualization with all sections', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.getByText('Result Visualization')).toBeInTheDocument();
    expect(screen.getByText('Latency Duration')).toBeInTheDocument();
    expect(screen.getByText('Variance Detection')).toBeInTheDocument();
    expect(screen.getByText('Content Hash Signature')).toBeInTheDocument();
  });

  it('should display latency duration', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.getByText('1.23s')).toBeInTheDocument();
  });

  it('should display latency in milliseconds for values under 1000ms', () => {
    render(<ResultVisualization result={mockResult} latency={500} />);

    expect(screen.getByText('500ms')).toBeInTheDocument();
  });

  it('should display "N/A" for null latency', () => {
    render(<ResultVisualization result={mockResult} latency={null} />);

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('should display "Yes" when change is detected', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    const varianceText = screen.getByText('Yes');
    expect(varianceText).toBeInTheDocument();
    expect(varianceText).toHaveClass('text-green-600');
  });

  it('should display "No" when change is not detected', () => {
    const resultNoChange: TriggerSourceResponse = {
      ...mockResult,
      changeDetected: false,
    };

    render(<ResultVisualization result={resultNoChange} latency={1234} />);

    const varianceText = screen.getByText('No');
    expect(varianceText).toBeInTheDocument();
    expect(varianceText).toHaveClass('text-gray-500');
  });

  it('should display fetched at timestamp', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.getByText(/fetched at/i)).toBeInTheDocument();
  });

  it('should display policy version ID when available', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.getByText(/version id/i)).toBeInTheDocument();
    expect(screen.getByText('version-1')).toBeInTheDocument();
  });

  it('should display policy change ID when available', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.getByText(/change id/i)).toBeInTheDocument();
    expect(screen.getByText('change-1')).toBeInTheDocument();
  });

  it('should display error message when error occurs', () => {
    const resultWithError: TriggerSourceResponse = {
      ...mockResult,
      success: false,
      error: 'Network timeout',
    };

    render(<ResultVisualization result={resultWithError} latency={1234} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
  });

  it('should not display error section when no error', () => {
    render(<ResultVisualization result={mockResult} latency={1234} />);

    expect(screen.queryByText('Error')).not.toBeInTheDocument();
  });
});

