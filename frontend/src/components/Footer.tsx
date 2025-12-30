/**
 * Footer Component
 * Fixed footer displaying real-time system status via scrolling marquee
 */

import React, { useState, useEffect } from 'react';
import { getStatus } from '../services/api';

interface SystemStatus {
  sources: Array<{
    id: string;
    name: string;
    status: string;
    last_checked_at: string | null;
  }>;
  statistics: {
    total_sources: number;
    healthy_sources: number;
    error_sources: number;
    stale_sources: number;
    never_checked_sources: number;
  };
  last_daily_job_run: string | null;
}

const Footer: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async (): Promise<void> => {
      try {
        const data = await getStatus();
        setStatus(data as SystemStatus);
        setError(null);
      } catch (err) {
        setError('Failed to load status');
        // Use mock data as fallback
        setStatus({
          sources: [],
          statistics: {
            total_sources: 0,
            healthy_sources: 0,
            error_sources: 0,
            stale_sources: 0,
            never_checked_sources: 0,
          },
          last_daily_job_run: null,
        });
      }
    };

    fetchStatus();
    // Refresh status every 30 seconds
    const interval = setInterval(fetchStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatStatusText = (): string => {
    if (!status) {
      return 'Loading system status...';
    }

    const stats = status.statistics;
    const parts: string[] = [];

    parts.push(`Total Sources: ${stats.total_sources}`);
    parts.push(`Healthy: ${stats.healthy_sources}`);
    if (stats.error_sources > 0) {
      parts.push(`Errors: ${stats.error_sources}`);
    }
    if (stats.stale_sources > 0) {
      parts.push(`Stale: ${stats.stale_sources}`);
    }
    if (stats.never_checked_sources > 0) {
      parts.push(`Never Checked: ${stats.never_checked_sources}`);
    }

    if (status.last_daily_job_run) {
      const lastRun = new Date(status.last_daily_job_run);
      parts.push(`Last Job Run: ${lastRun.toLocaleString()}`);
    }

    return parts.join(' | ');
  };

  const statusText = formatStatusText();
  // Duplicate text for seamless scrolling
  const marqueeText = `${statusText} • ${statusText} • `;

  return (
    <footer className="fixed bottom-0 left-0 right-0 border-t-2 border-foreground bg-background z-30">
      <div className="overflow-hidden h-12 flex items-center">
        <div
          className="whitespace-nowrap font-mono text-xs uppercase tracking-widest"
          style={{
            display: 'inline-block',
            paddingLeft: '100%',
            animation: 'marquee 30s linear infinite',
          }}
        >
          {marqueeText}
        </div>
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
    </footer>
  );
};

export default Footer;

