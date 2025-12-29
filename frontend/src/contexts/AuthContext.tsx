/**
 * Authentication Context
 * Provides authentication state and methods throughout the application
 */
/* eslint-disable react-refresh/only-export-components */

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getToken } from '../services/api';
import { getCurrentUser, logout as authLogout } from '../services/auth';

/**
 * User information type
 */
export interface User {
  id: string;
  username: string;
  is_active: boolean;
  created_at?: string;
}

/**
 * Authentication context value
 */
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

/**
 * Create the auth context
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider component props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider component
 * Manages authentication state and provides auth methods to children
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  /**
   * Check if user is authenticated by validating token
   */
  const checkAuth = async (): Promise<void> => {
    setLoading(true);
    
    try {
      const token = getToken();
      
      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
        return;
      }

      // Try to get current user to validate token
      const userData = await getCurrentUser();
      
      if (userData) {
        // If we got user data, token is valid
        setUser(userData as User);
        setIsAuthenticated(true);
      } else {
        // Token exists but validation endpoint doesn't exist or failed
        // For now, if token exists, consider user authenticated
        // The API will return 401 if token is invalid
        setIsAuthenticated(true);
        // Set a minimal user object if we can't get full user data
        setUser({ id: 'unknown', username: 'user', is_active: true });
      }
    } catch {
      // Token is invalid or expired
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Login function
   * This will be set by the auth service after successful login
   */
  const login = async (username: string, password: string): Promise<{ success: boolean; error?: string }> => {
    // Import here to avoid circular dependency
    const { login: authLogin } = await import('../services/auth');
    const result = await authLogin(username, password);
    
    if (result.success) {
      // Re-check auth state after successful login
      await checkAuth();
    }
    
    return result;
  };

  /**
   * Logout function
   */
  const handleLogout = async (): Promise<void> => {
    await authLogout();
    setIsAuthenticated(false);
    setUser(null);
  };

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    isAuthenticated,
    user,
    loading,
    login,
    logout: handleLogout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * useAuth hook
 * Provides access to authentication context
 * 
 * @returns AuthContextType
 * @throws Error if used outside AuthProvider
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

