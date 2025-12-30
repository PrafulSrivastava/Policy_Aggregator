/**
 * Terminal Output Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TerminalOutput from '../../../components/diagnostics/TerminalOutput';

describe('TerminalOutput Component', () => {
  it('should render empty terminal with waiting message', () => {
    render(<TerminalOutput logs={[]} />);
    
    expect(screen.getByText('Terminal Output')).toBeInTheDocument();
    expect(screen.getByText(/waiting for operation/i)).toBeInTheDocument();
  });

  it('should render log messages', () => {
    const logs = [
      '[SYSTEM] Initializing fetch operation...',
      '[NETWORK] Establishing connection...',
      '[FETCH] Content retrieved successfully',
    ];

    render(<TerminalOutput logs={logs} />);

    expect(screen.getByText('[SYSTEM] Initializing fetch operation...')).toBeInTheDocument();
    expect(screen.getByText('[NETWORK] Establishing connection...')).toBeInTheDocument();
    expect(screen.getByText('[FETCH] Content retrieved successfully')).toBeInTheDocument();
  });

  it('should render multiple log entries', () => {
    const logs = Array.from({ length: 10 }, (_, i) => `Log message ${i + 1}`);

    render(<TerminalOutput logs={logs} />);

    logs.forEach((log) => {
      expect(screen.getByText(log)).toBeInTheDocument();
    });
  });

  it('should have terminal styling classes', () => {
    const { container } = render(<TerminalOutput logs={[]} />);
    
    const terminalElement = container.querySelector('.bg-black');
    expect(terminalElement).toBeInTheDocument();
    expect(terminalElement).toHaveClass('font-mono');
  });
});

