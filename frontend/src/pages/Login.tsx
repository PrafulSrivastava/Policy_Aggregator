/**
 * Login Page Component
 * Handles user authentication with User ID (Email) and Access Key (Password)
 */

import React, { useState, useEffect } from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Alert from '../components/Alert';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Login Page Component
 */
const Login: React.FC = () => {
  const [userId, setUserId] = useState('');
  const [accessKey, setAccessKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{ userId?: string; accessKey?: string }>({});
  
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
   * Validate form fields
   */
  const validateForm = (): boolean => {
    const errors: { userId?: string; accessKey?: string } = {};

    if (!userId.trim()) {
      errors.userId = 'User ID is required';
    }

    if (!accessKey) {
      errors.accessKey = 'Access Key is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setError(null);
    setValidationErrors({});

    // Validate form
    if (!validateForm()) {
      setError('Missing Credentials');
      return;
    }

    setLoading(true);

    // Attempt login
    const result = await login(userId.trim(), accessKey);

    if (result.success) {
      // Clear any errors
      setError(null);
      // Redirect to dashboard (HashRouter will handle /#/dashboard automatically)
      const redirectTo = searchParams.get('redirect') || '/';
      navigate(redirectTo, { replace: true });
    } else {
      setError(result.error || 'Access Denied');
      setLoading(false);
    }
  };

  /**
   * Check if form can be submitted
   */
  const canSubmit = (): boolean => {
    return userId.trim().length > 0 && accessKey.length > 0 && !loading;
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
            <Alert
              type="error"
              message={error}
              onClose={() => setError(null)}
            />
          )}

          {loading ? (
            <LoadingSpinner message="Initializing Session..." />
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* User ID Input */}
              <div>
                <label htmlFor="userId" className="block text-sm font-medium mb-2 uppercase tracking-widest">
                  User ID
                </label>
                <input
                  id="userId"
                  type="text"
                  value={userId}
                  onChange={(e) => {
                    setUserId(e.target.value);
                    // Clear validation error when user types
                    if (validationErrors.userId) {
                      setValidationErrors({ ...validationErrors, userId: undefined });
                    }
                    // Clear general error when user types
                    if (error) {
                      setError(null);
                    }
                  }}
                  className={`input ${validationErrors.userId ? 'border-red-500' : ''}`}
                  placeholder="Enter your User ID"
                  disabled={loading}
                  autoComplete="username"
                />
                {validationErrors.userId && (
                  <p className="mt-1 text-sm text-red-500" role="alert">
                    {validationErrors.userId}
                  </p>
                )}
              </div>

              {/* Access Key Input */}
              <div>
                <label htmlFor="accessKey" className="block text-sm font-medium mb-2 uppercase tracking-widest">
                  Access Key
                </label>
                <input
                  id="accessKey"
                  type="password"
                  value={accessKey}
                  onChange={(e) => {
                    setAccessKey(e.target.value);
                    // Clear validation error when user types
                    if (validationErrors.accessKey) {
                      setValidationErrors({ ...validationErrors, accessKey: undefined });
                    }
                    // Clear general error when user types
                    if (error) {
                      setError(null);
                    }
                  }}
                  className={`input ${validationErrors.accessKey ? 'border-red-500' : ''}`}
                  placeholder="Enter your Access Key"
                  disabled={loading}
                  autoComplete="current-password"
                />
                {validationErrors.accessKey && (
                  <p className="mt-1 text-sm text-red-500" role="alert">
                    {validationErrors.accessKey}
                  </p>
                )}
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className="btn-primary w-full"
                disabled={!canSubmit()}
              >
                Initialize Session
              </button>
            </form>
          )}

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

