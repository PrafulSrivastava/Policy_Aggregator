/**
 * Marquee Component
 * High-speed scrolling marquee displaying aggregate statistics
 */

import React from 'react';

interface MarqueeProps {
  statistics: {
    totalRoutes: number;
    activeSources: number;
    changesLast7Days: number;
  };
}

const Marquee: React.FC<MarqueeProps> = ({ statistics }) => {
  const statsText = `Total Routes: ${statistics.totalRoutes} | Active Sources: ${statistics.activeSources} | Detected Variances (7d): ${statistics.changesLast7Days}`;
  
  // Duplicate text for seamless scrolling
  const marqueeText = `${statsText} • ${statsText} • `;

  return (
    <div className="border-b-2 border-foreground bg-background overflow-hidden h-16 flex items-center">
      <div
        className="whitespace-nowrap font-mono text-sm uppercase tracking-widest"
        style={{
          display: 'inline-block',
          paddingLeft: '100%',
          animation: 'marquee 20s linear infinite',
        }}
      >
        {marqueeText}
      </div>
      <style>{`
        @keyframes marquee {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
      `}</style>
    </div>
  );
};

export default Marquee;

