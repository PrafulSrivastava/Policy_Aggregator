/**
 * Navigation Component
 * Main navigation bar with logout functionality
 */

import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Navigation: React.FC = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <nav className="border-b-2 border-foreground bg-background">
      <div className="max-w-6xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-2xl font-display font-bold tracking-tight hover:underline">
              Policy Aggregator
            </Link>
            <div className="flex items-center space-x-6">
              <Link
                to="/"
                className={`text-sm uppercase tracking-widest hover:underline ${
                  location.pathname === '/' ? 'font-bold underline' : ''
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/routes"
                className={`text-sm uppercase tracking-widest hover:underline ${
                  location.pathname === '/routes' ? 'font-bold underline' : ''
                }`}
              >
                Routes
              </Link>
              <Link
                to="/sources"
                className={`text-sm uppercase tracking-widest hover:underline ${
                  location.pathname === '/sources' ? 'font-bold underline' : ''
                }`}
              >
                Sources
              </Link>
              <Link
                to="/changes"
                className={`text-sm uppercase tracking-widest hover:underline ${
                  location.pathname === '/changes' ? 'font-bold underline' : ''
                }`}
              >
                Changes
              </Link>
              <Link
                to="/settings/notifications"
                className={`text-sm uppercase tracking-widest hover:underline ${
                  location.pathname.startsWith('/settings') ? 'font-bold underline' : ''
                }`}
              >
                Settings
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {user && (
              <span className="text-sm text-mutedForeground uppercase tracking-widest">
                {user.username}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="btn-ghost text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;

