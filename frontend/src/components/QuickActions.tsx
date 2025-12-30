/**
 * Quick Actions Component
 * Displays quick action cards for Route Index and Source Nodes
 */

import React from 'react';
import { Link } from 'react-router-dom';

interface QuickActionsProps {
  totalRoutes: number;
  activeSources: number;
  loading?: boolean;
}

const QuickActions: React.FC<QuickActionsProps> = ({ totalRoutes, activeSources, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <p className="text-mutedForeground">Loading...</p>
        </div>
        <div className="card">
          <p className="text-mutedForeground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Route Index Card */}
      <Link
        to="/routes"
        className="card hover:bg-foreground hover:text-background transition-colors duration-100 cursor-pointer"
      >
        <h3 className="text-2xl font-display font-bold mb-2 tracking-tight">
          Route Index
        </h3>
        <p className="text-5xl font-display font-bold mb-2">
          {totalRoutes}
        </p>
        <p className="text-sm text-mutedForeground uppercase tracking-widest">
          Total Routes
        </p>
        <p className="text-sm mt-4 uppercase tracking-widest">
          Route Configuration →
        </p>
      </Link>

      {/* Source Nodes Card */}
      <Link
        to="/sources"
        className="card hover:bg-foreground hover:text-background transition-colors duration-100 cursor-pointer"
      >
        <h3 className="text-2xl font-display font-bold mb-2 tracking-tight">
          Source Nodes
        </h3>
        <p className="text-5xl font-display font-bold mb-2">
          {activeSources}
        </p>
        <p className="text-sm text-mutedForeground uppercase tracking-widest">
          Active Sources
        </p>
        <p className="text-sm mt-4 uppercase tracking-widest">
          Source Management →
        </p>
      </Link>
    </div>
  );
};

export default QuickActions;

