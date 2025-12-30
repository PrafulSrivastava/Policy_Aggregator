/**
 * Dashboard Page Component
 * Enhanced dashboard with marquee, recent signals, and quick actions
 */

import React, { useState, useEffect } from 'react';
import Marquee from '../components/Marquee';
import RecentSignals from '../components/RecentSignals';
import QuickActions from '../components/QuickActions';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import { getDashboardStats, getRecentChanges, type DashboardStats, type ChangeItem } from '../services/dashboard';

const Dashboard: React.FC = () => {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [recentChanges, setRecentChanges] = useState<ChangeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async (): Promise<void> => {
    try {
      setError(null);
      
      // Fetch dashboard statistics
      const stats = await getDashboardStats();
      if (!stats) {
        setError('Failed to load dashboard statistics');
        setLoading(false);
        return;
      }
      setDashboardStats(stats);

      // Fetch recent changes
      const changesResponse = await getRecentChanges(3);
      if (changesResponse) {
        setRecentChanges(changesResponse.items);
      } else {
        // Don't fail the whole dashboard if changes fail
        console.warn('Failed to load recent changes');
      }

      setLoading(false);
    } catch (err) {
      setError('Failed to load dashboard data');
      setLoading(false);
      console.error('Dashboard data fetch error:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Refresh statistics every 30 seconds
    const interval = setInterval(() => {
      fetchDashboardData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading && !dashboardStats) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <LoadingSpinner message="Loading dashboard..." />
        </div>
      </div>
    );
  }

  if (error && !dashboardStats) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="max-w-6xl mx-auto">
          <ErrorMessage
            message={error}
            onRetry={fetchDashboardData}
            retryLabel="Retry"
          />
        </div>
      </div>
    );
  }

  if (!dashboardStats) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Marquee at top */}
      <Marquee
        statistics={{
          totalRoutes: dashboardStats.totalRoutes,
          activeSources: dashboardStats.activeSources,
          changesLast7Days: dashboardStats.changesLast7Days,
        }}
      />

      {/* Main content */}
      <div className="p-6">
        <div className="max-w-6xl mx-auto space-y-8">
          <h1 className="text-7xl font-display font-bold tracking-tight">
            Dashboard
          </h1>

          {/* Recent Signals Feed */}
          <RecentSignals
            changes={recentChanges}
            loading={loading}
            error={error}
          />

          {/* Quick Actions */}
          <QuickActions
            totalRoutes={dashboardStats.totalRoutes}
            activeSources={dashboardStats.activeSources}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

