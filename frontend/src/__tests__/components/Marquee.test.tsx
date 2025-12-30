/**
 * Marquee Component Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Marquee from '../../components/Marquee';

describe('Marquee Component', () => {
  it('should render marquee with statistics', () => {
    const statistics = {
      totalRoutes: 5,
      activeSources: 8,
      changesLast7Days: 3,
    };

    render(<Marquee statistics={statistics} />);

    expect(screen.getByText(/total routes: 5/i)).toBeInTheDocument();
    expect(screen.getByText(/active sources: 8/i)).toBeInTheDocument();
    expect(screen.getByText(/detected variances \(7d\): 3/i)).toBeInTheDocument();
  });

  it('should have scrolling animation', () => {
    const statistics = {
      totalRoutes: 5,
      activeSources: 8,
      changesLast7Days: 3,
    };

    const { container } = render(<Marquee statistics={statistics} />);
    
    const marqueeElement = container.querySelector('[style*="animation"]');
    expect(marqueeElement).toBeInTheDocument();
  });
});

