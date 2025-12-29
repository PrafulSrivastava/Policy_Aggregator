/**
 * Login Page Component
 * Handles user authentication with email/password
 */

import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Login Page Component
 */
const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const redirectTo = searchParams.get('redirect') || '/';
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, navigate, searchParams]);

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    // Validation
    if (!username.trim()) {
      setError('Username is required');
      setLoading(false);
      return;
    }

    if (!password) {
      setError('Password is required');
      setLoading(false);
      return;
    }

    // Optional: Validate email format (if username is expected to be email)
    // if (!validateEmail(username)) {
    //   setError('Please enter a valid email address');
    //   setLoading(false);
    //   return;
    // }

    // Attempt login
    const result = await login(username, password);

    if (result.success) {
      // Redirect to intended page or dashboard
      const redirectTo = searchParams.get('redirect') || '/';
      navigate(redirectTo, { replace: true });
    } else {
      setError(result.error || 'Login failed. Please check your credentials.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <div className="w-full max-w-md">
        {/* Login Form Card */}
        <div className="card">
          <h1 className="text-5xl font-display font-bold mb-8 text-center tracking-tight">
            Login
          </h1>

          {error && (
            <div className="mb-6 p-4 bg-foreground text-background border-2 border-foreground">
              <p className="text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username/Email Input */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium mb-2 uppercase tracking-widest">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input"
                placeholder="Enter your username"
                disabled={loading}
                autoComplete="username"
                required
              />
            </div>

            {/* Password Input */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-2 uppercase tracking-widest">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="Enter your password"
                disabled={loading}
                autoComplete="current-password"
                required
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          {/* OAuth Section (Placeholder for future implementation) */}
          {/* 
          <div className="mt-8 pt-8 border-t-2 border-foreground">
            <p className="text-sm text-mutedForeground text-center mb-4 uppercase tracking-widest">
              Or continue with
            </p>
            <div className="space-y-3">
              <button
                type="button"
                className="btn-secondary w-full"
                disabled
              >
                Google (Coming Soon)
              </button>
              <button
                type="button"
                className="btn-secondary w-full"
                disabled
              >
                GitHub (Coming Soon)
              </button>
            </div>
          </div>
          */}
        </div>
      </div>
    </div>
  );
};

export default Login;

