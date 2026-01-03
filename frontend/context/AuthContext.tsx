import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  initiateGoogleOAuth: () => void;
  checkOAuthAvailability: () => Promise<boolean>;
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
    const checkAuth = async () => {
      console.log('[AUTH] useEffect running, checking for existing session...');
      
      // First, check for OAuth token in URL (from OAuth callback redirect)
      // With hash routing, query params can be in either location.search or location.hash
      let oauthToken: string | null = null;
      
      console.log('[AUTH] Checking for token in URL...');
      console.log('[AUTH] window.location.search:', window.location.search);
      console.log('[AUTH] window.location.hash:', window.location.hash);
      
      // Check regular query params first
      const urlParams = new URLSearchParams(window.location.search);
      oauthToken = urlParams.get('token');
      if (oauthToken) {
        console.log('[AUTH] Token found in window.location.search');
      }
      
      // If not found, check hash fragment (for hash routing like /#/?token=...)
      if (!oauthToken && window.location.hash) {
        const hashMatch = window.location.hash.match(/[?&]token=([^&]+)/);
        if (hashMatch) {
          oauthToken = decodeURIComponent(hashMatch[1]);
          console.log('[AUTH] Token found in hash fragment');
        }
      }
      
      if (oauthToken) {
        console.log('[AUTH] ✅ OAuth token found in URL, storing in localStorage...');
        localStorage.setItem('auth_token', oauthToken);
        // Clear token from URL - remove from hash if present
        let newHash = window.location.hash.replace(/[?&]token=[^&]*/, '').replace(/[?&]$/, '');
        if (newHash === '#') newHash = '#/';
        const newUrl = window.location.pathname + window.location.search + newHash;
        window.history.replaceState({}, '', newUrl);
        console.log('[AUTH] Token stored and URL cleaned');
        setIsAuthenticated(true);
        setIsLoading(false);
        return;
      }
      
      // Check for existing session - first check localStorage
      const token = localStorage.getItem('auth_token');
      console.log('[AUTH] Token found in localStorage:', token ? 'Yes (length: ' + token.length + ')' : 'No');
      
      if (token) {
        console.log('[AUTH] ✅ Token found in localStorage, setting authenticated to true');
        setIsAuthenticated(true);
        setIsLoading(false);
        return;
      }
      
      // If no localStorage token, check if we have a cookie (from OAuth)
      // We can't read httpOnly cookies directly, so we verify by making an API call
      try {
        console.log('[AUTH] No localStorage token, checking for cookie-based auth...');
        const isAuthenticated = await api.verifyAuth();
        if (isAuthenticated) {
          console.log('[AUTH] ✅ Cookie-based auth verified, setting authenticated to true');
          setIsAuthenticated(true);
        } else {
          console.log('[AUTH] ⚠️ No authentication found');
        }
      } catch (error) {
        console.log('[AUTH] ⚠️ Auth verification failed, user not authenticated');
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
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

  const signup = async (email: string, password: string) => {
    console.log('[AUTH] Signup attempt for email:', email);
    try {
      setError(null);
      setIsLoading(true);
      console.log('[AUTH] Calling API signup...');
      const response = await api.signup({ email, password });
      console.log('[AUTH] ✅ Signup successful, received token');
      localStorage.setItem('auth_token', response.access_token);
      setIsAuthenticated(true);
      console.log('[AUTH] Authentication state updated');
    } catch (err: any) {
      console.error('[AUTH] ❌ Signup failed:', err);
      const errorMessage = err.response?.data?.detail || 'Signup failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
      console.log('[AUTH] Signup process completed, isLoading set to false');
    }
  };

  const initiateGoogleOAuth = () => {
    console.log('[AUTH] Initiating Google OAuth...');
    api.initiateGoogleOAuth();
  };

  const checkOAuthAvailability = async (): Promise<boolean> => {
    console.log('[AUTH] Checking OAuth availability...');
    try {
      const available = await api.checkOAuthAvailability();
      console.log('[AUTH] OAuth available:', available);
      return available;
    } catch (error) {
      console.error('[AUTH] Error checking OAuth availability:', error);
      return false;
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
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      login, 
      signup, 
      initiateGoogleOAuth,
      checkOAuthAvailability,
      logout, 
      isLoading, 
      error 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};