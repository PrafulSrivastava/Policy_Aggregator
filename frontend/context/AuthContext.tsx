import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  console.log('[AUTH] AuthProvider initializing...');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[AUTH] useEffect running, checking for existing session...');
    // Check for existing session
    const token = localStorage.getItem('auth_token');
    console.log('[AUTH] Token found in localStorage:', token ? 'Yes (length: ' + token.length + ')' : 'No');
    if (token) {
      console.log('[AUTH] ✅ Token found, setting authenticated to true');
      setIsAuthenticated(true);
    } else {
      console.log('[AUTH] ⚠️ No token found, user not authenticated');
    }
    console.log('[AUTH] Setting isLoading to false');
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    console.log('[AUTH] Login attempt for username:', username);
    try {
      setError(null);
      setIsLoading(true);
      console.log('[AUTH] Calling API login...');
      const response = await api.login({ username, password });
      console.log('[AUTH] ✅ Login successful, received token');
      localStorage.setItem('auth_token', response.access_token);
      setIsAuthenticated(true);
      console.log('[AUTH] Authentication state updated');
    } catch (err: any) {
      console.error('[AUTH] ❌ Login failed:', err);
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
      console.log('[AUTH] Login process completed, isLoading set to false');
    }
  };

  const logout = async () => {
    console.log('[AUTH] Logout called');
    try {
      await api.logout();
      console.log('[AUTH] ✅ Logout API call successful');
    } catch (err) {
      console.warn('[AUTH] ⚠️ Logout API call failed, continuing with local logout:', err);
      // Continue with logout even if API call fails
    } finally {
      localStorage.removeItem('auth_token');
      setIsAuthenticated(false);
      setError(null);
      console.log('[AUTH] Logout completed, token removed');
    }
  };

  console.log('[AUTH] Rendering AuthProvider with state:', { isAuthenticated, isLoading, hasError: !!error });
  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, isLoading, error }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};