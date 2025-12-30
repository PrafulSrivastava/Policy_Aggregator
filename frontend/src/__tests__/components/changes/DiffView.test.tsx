/**
 * DiffView Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DiffView from '../../../components/changes/DiffView';

describe('DiffView Component', () => {
  it('should render diff with added lines', () => {
    const diff = '--- old\n+++ new\n@@ -1,2 +1,3 @@\n line1\n+line2\n line3';
    
    render(<DiffView diff={diff} />);

    const addedLine = screen.getByText(/line2/);
    expect(addedLine).toBeInTheDocument();
    expect(addedLine.closest('div')).toHaveClass('bg-green-100');
  });

  it('should render diff with removed lines and strikethrough', () => {
    const diff = '--- old\n+++ new\n@@ -1,3 +1,2 @@\n line1\n-line2\n line3';
    
    render(<DiffView diff={diff} />);

    const removedLine = screen.getByText(/line2/);
    expect(removedLine).toBeInTheDocument();
    expect(removedLine.closest('div')).toHaveClass('bg-red-100');
    expect(removedLine.closest('div')).toHaveClass('line-through');
  });

  it('should render diff with context lines', () => {
    const diff = '--- old\n+++ new\n@@ -1,3 +1,3 @@\n line1\n line2\n line3';
    
    render(<DiffView diff={diff} />);

    const contextLine = screen.getByText(/line2/);
    expect(contextLine).toBeInTheDocument();
    expect(contextLine.closest('div')).not.toHaveClass('bg-green-100');
    expect(contextLine.closest('div')).not.toHaveClass('bg-red-100');
  });

  it('should render diff headers', () => {
    const diff = '--- old\n+++ new\n@@ -1,3 +1,3 @@\n line1';
    
    render(<DiffView diff={diff} />);

    expect(screen.getByText(/--- old/)).toBeInTheDocument();
    expect(screen.getByText(/\+\+\+ new/)).toBeInTheDocument();
  });

  it('should use monospace font', () => {
    const diff = '--- old\n+++ new\n line1';
    
    const { container } = render(<DiffView diff={diff} />);
    const pre = container.querySelector('pre');
    
    expect(pre).toHaveClass('font-mono');
  });

  it('should apply custom className', () => {
    const diff = '--- old\n+++ new\n line1';
    
    const { container } = render(<DiffView diff={diff} className="custom-class" />);
    const wrapper = container.firstChild;
    
    expect(wrapper).toHaveClass('custom-class');
  });

  it('should handle empty diff', () => {
    render(<DiffView diff="" />);
    
    // Should render without errors
    const container = screen.getByRole('generic');
    expect(container).toBeInTheDocument();
  });

  it('should handle complex unified diff', () => {
    const diff = `--- old.txt
+++ new.txt
@@ -1,5 +1,5 @@
 unchanged line
-removed line
+added line
 unchanged line
 context line
 another context`;
    
    render(<DiffView diff={diff} />);

    expect(screen.getByText(/removed line/)).toBeInTheDocument();
    expect(screen.getByText(/added line/)).toBeInTheDocument();
    // Check that context lines are rendered (there should be at least one)
    const contextLines = screen.getAllByText(/unchanged line|context line|another context/);
    expect(contextLines.length).toBeGreaterThan(0);
  });
});

