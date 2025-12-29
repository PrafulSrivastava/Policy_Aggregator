/**
 * SummaryView Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SummaryView from '../../../components/ai/SummaryView';

describe('SummaryView Component', () => {
  it('should render summary text', () => {
    const summary = 'This is a test summary of policy changes.';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/AI-Generated Summary/i)).toBeInTheDocument();
    expect(screen.getByText(/This is a test summary/)).toBeInTheDocument();
  });

  it('should display generated timestamp when provided', () => {
    const summary = 'Test summary';
    const generatedAt = '2025-01-27T10:00:00Z';
    
    render(<SummaryView summary={summary} generatedAt={generatedAt} />);

    expect(screen.getByText(/Generated:/i)).toBeInTheDocument();
  });

  it('should display AI disclaimer', () => {
    const summary = 'Test summary';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/AI-generated and may contain inaccuracies/i)).toBeInTheDocument();
  });

  it('should parse and display Key Changes section', () => {
    const summary = 'Key Changes: Updated visa requirements for students.\n\nImpact: Affects applications.\n\nContext: Policy change.';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/Key Changes/i)).toBeInTheDocument();
    expect(screen.getByText(/Updated visa requirements for students/i)).toBeInTheDocument();
  });

  it('should parse and display Impact section', () => {
    const summary = 'Key Changes: Updated requirements.\n\nImpact: Affects student visa applications.\n\nContext: Policy change.';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/Impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Affects student visa applications/i)).toBeInTheDocument();
  });

  it('should parse and display Context section', () => {
    const summary = 'Key Changes: Updated requirements.\n\nImpact: Affects applications.\n\nContext: Policy change effective immediately.';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/Context/i)).toBeInTheDocument();
    expect(screen.getByText(/Policy change effective immediately/i)).toBeInTheDocument();
  });

  it('should display raw summary when no sections are parsed', () => {
    const summary = 'This is a simple summary without structured sections.';
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/This is a simple summary/)).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const summary = 'Test summary';
    
    const { container } = render(<SummaryView summary={summary} className="custom-class" />);
    const wrapper = container.firstChild;
    
    expect(wrapper).toHaveClass('custom-class');
  });

  it('should handle empty summary', () => {
    render(<SummaryView summary="" />);

    expect(screen.getByText(/AI-Generated Summary/i)).toBeInTheDocument();
  });

  it('should handle summary with multiple sections', () => {
    const summary = `Key Changes: 
- Updated visa requirements
- New documentation needed

Impact: 
This affects all student visa applications.

Context: 
The policy change was announced on January 27, 2025.`;
    
    render(<SummaryView summary={summary} />);

    expect(screen.getByText(/Key Changes/i)).toBeInTheDocument();
    expect(screen.getByText(/Impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Context/i)).toBeInTheDocument();
    expect(screen.getByText(/Updated visa requirements/i)).toBeInTheDocument();
    expect(screen.getByText(/affects all student visa applications/i)).toBeInTheDocument();
  });

  it('should preserve whitespace in summary text', () => {
    const summary = 'Key Changes:\n\nLine 1\nLine 2';
    
    const { container } = render(<SummaryView summary={summary} />);
    const textElement = container.querySelector('.whitespace-pre-wrap');
    
    expect(textElement).toBeInTheDocument();
  });
});

