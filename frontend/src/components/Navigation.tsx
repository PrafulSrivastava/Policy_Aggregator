/**
 * Navigation Component
 * Main navigation bar with logout functionality and responsive mobile menu
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Navigation: React.FC = () => {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate('/login', { replace: true });
  };

  const toggleMobileMenu = (): void => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = (): void => {
    setIsMobileMenuOpen(false);
  };

  const isActive = (path: string): boolean => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const navLinks = [
    { to: '/', label: 'Dashboard' },
    { to: '/routes', label: 'Routes' },
    { to: '/sources', label: 'Sources' },
    { to: '/changes', label: 'Changes' },
    { to: '/settings/notifications', label: 'Settings' },
  ];

  return (
    <nav className="border-b-2 border-foreground bg-background">
      <div className="max-w-6xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-2xl font-display font-bold tracking-tight hover:underline">
              Policy Aggregator
            </Link>
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-6">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`text-sm uppercase tracking-widest hover:underline ${
                    isActive(link.to) ? 'font-bold underline' : ''
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {/* Desktop User Info */}
            <div className="hidden md:flex items-center space-x-4">
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
            {/* Mobile Hamburger Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="md:hidden btn-ghost p-2"
              aria-label="Toggle menu"
              aria-expanded={isMobileMenuOpen}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                {isMobileMenuOpen ? (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                ) : (
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Slide-in Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-64 bg-background border-l-2 border-foreground z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-display font-bold tracking-tight">Menu</h2>
            <button
              onClick={closeMobileMenu}
              className="btn-ghost p-2"
              aria-label="Close menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <nav className="flex flex-col space-y-4">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={closeMobileMenu}
                className={`text-sm uppercase tracking-widest hover:underline py-2 ${
                  isActive(link.to) ? 'font-bold underline' : ''
                }`}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-4 border-t-2 border-foreground">
              {user && (
                <div className="mb-4">
                  <span className="text-sm text-mutedForeground uppercase tracking-widest">
                    {user.username}
                  </span>
                </div>
              )}
              <button
                onClick={async () => {
                  await handleLogout();
                  closeMobileMenu();
                }}
                className="btn-ghost text-sm w-full text-left"
              >
                Logout
              </button>
            </div>
          </nav>
        </div>
      </div>
      
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}
    </nav>
  );
};

export default Navigation;

