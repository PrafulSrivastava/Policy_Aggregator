/**
 * Dashboard Page Component
 * Main dashboard/home page (placeholder for now)
 */

import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-7xl font-display font-bold mb-8 tracking-tight">
          Dashboard
        </h1>
        <p className="text-xl font-body text-mutedForeground">
          Welcome to the Policy Aggregator admin interface.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;

