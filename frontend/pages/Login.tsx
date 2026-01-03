import React, { useState, useEffect } from 'react';
import { Button, Card, Input } from '../components/Common';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GoogleOAuthButton from '../components/auth/GoogleOAuthButton';

const Login: React.FC = () => {
  console.log('[LOGIN] Login page component rendering...');
  const { login, initiateGoogleOAuth, checkOAuthAvailability } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isOAuthLoading, setIsOAuthLoading] = useState(false);
  const [isOAuthAvailable, setIsOAuthAvailable] = useState(false);
  // TODO: Remove this debug flag after testing
  // Set to true to always show OAuth button for testing
  const FORCE_SHOW_OAUTH = true; // Temporarily enabled for UI testing
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Check OAuth availability on mount
  useEffect(() => {
    const checkOAuth = async () => {
      console.log('[LOGIN] Checking OAuth availability...');
      try {
        const available = await checkOAuthAvailability();
        console.log('[LOGIN] OAuth available:', available);
        setIsOAuthAvailable(available);
      } catch (error) {
        console.error('[LOGIN] Error checking OAuth availability:', error);
        // On error, default to false (don't show button)
        // But log the error for debugging
        setIsOAuthAvailable(false);
      }
    };
    checkOAuth();
  }, [checkOAuthAvailability]);

  // Handle OAuth errors from URL params
  useEffect(() => {
    const oauthError = searchParams.get('error');
    if (oauthError) {
      let errorMessage = 'Authentication failed';
      switch (oauthError) {
        case 'oauth_denied':
          errorMessage = 'Access denied. Please try again or use password login.';
          break;
        case 'oauth_invalid':
          errorMessage = 'Invalid authentication. Please try again.';
          break;
        case 'oauth_failed':
          errorMessage = 'Authentication failed. Please try again or use password login.';
          break;
        default:
          errorMessage = 'Authentication error. Please try again.';
      }
      setError(errorMessage);
      // Clear the error from URL
      navigate('/login', { replace: true });
    }
  }, [searchParams, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[LOGIN] Form submitted with email:', email);
    setError('');
    setIsLoading(true);

    try {
      console.log('[LOGIN] Calling login function...');
      await login(email, password);
      console.log('[LOGIN] ✅ Login successful, navigating to dashboard...');
      navigate('/');
    } catch (err: any) {
      console.error('[LOGIN] ❌ Login failed:', err);
      const errorMessage = err.response?.data?.detail || 'Invalid username or password';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      console.log('[LOGIN] Login attempt completed');
    }
  };

  const handleGoogleOAuth = () => {
    console.log('[LOGIN] Google OAuth button clicked');
    setIsOAuthLoading(true);
    setError('');
    try {
      initiateGoogleOAuth();
      // The redirect will happen, so we don't need to handle the response
    } catch (err: any) {
      console.error('[LOGIN] ❌ OAuth initiation failed:', err);
      setError('Failed to initiate Google OAuth. Please try again.');
      setIsOAuthLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white font-sans">
      {/* Left Column: Brand / Aesthetics */}
      <div className="hidden lg:flex lg:w-1/2 bg-muted relative border-r-4 border-black items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-swiss-grid opacity-50"></div>
        {/* Abstract Bauhaus shapes */}
        <div className="absolute top-20 left-20 w-32 h-32 border-4 border-black rounded-full"></div>
        <div className="absolute bottom-20 right-20 w-64 h-64 border-4 border-accent rotate-45"></div>
        <div className="absolute top-1/2 left-1/2 w-[200%] h-1 bg-black -rotate-45 transform -translate-x-1/2 -translate-y-1/2"></div>
        
        <div className="relative z-10 p-12 max-w-lg">
          <h1 className="text-8xl font-black uppercase tracking-tighter leading-[0.85] text-black">
            Policy<br/>
            <span className="text-accent">Aggregator</span>
          </h1>
          <div className="mt-12 space-y-4 border-l-4 border-black pl-8">
            <p className="text-xl font-bold uppercase tracking-wide">Regulatory Intelligence</p>
            <p className="text-sm font-medium text-slate-600 max-w-md">
              Objective monitoring of global migration policies. Automated change detection. Precise impact assessment.
            </p>
          </div>
        </div>
      </div>

      {/* Right Column: Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-24 relative">
        <div className="absolute top-0 right-0 p-8">
           <span className="font-mono text-xs">V.2.4.0</span>
        </div>

        <div className="w-full max-w-md space-y-12">
          <div>
            <h2 className="text-4xl font-black uppercase tracking-tight mb-2">System Access</h2>
            <div className="h-1 w-24 bg-accent"></div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            <Input
              id="email"
              type="email"
              label="User Identifier"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="ADMIN@EXAMPLE.COM"
              autoFocus
              required
              className="bg-muted focus:bg-white"
            />
            
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                label="Access Key"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="bg-muted focus:bg-white"
              />
              <button
                type="button"
                className="absolute right-4 top-[2.2rem] text-black hover:text-accent transition-colors"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <div className="flex items-center">
              <input
                id="remember-me"
                type="checkbox"
                className="h-5 w-5 text-black focus:ring-accent border-2 border-black rounded-none"
              />
              <label htmlFor="remember-me" className="ml-3 block text-xs font-bold uppercase tracking-wider text-black">
                Maintain Session
              </label>
            </div>

            {error && (
              <div className="bg-accent text-white p-4 border-2 border-black flex items-center text-sm font-bold">
                <Lock className="w-4 h-4 mr-3" />
                {error.toUpperCase()}
              </div>
            )}

            {(() => {
              const shouldShowOAuth = isOAuthAvailable || FORCE_SHOW_OAUTH;
              console.log('[LOGIN] OAuth button render check:', { isOAuthAvailable, FORCE_SHOW_OAUTH, shouldShowOAuth });
              return shouldShowOAuth ? (
                <>
                  <GoogleOAuthButton 
                    onClick={handleGoogleOAuth}
                    isLoading={isOAuthLoading}
                    disabled={isLoading}
                  />
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t-2 border-black"></div>
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-white px-2 text-black font-bold tracking-wider">OR</span>
                    </div>
                  </div>
                </>
              ) : null;
            })()}

            <Button type="submit" className="w-full h-16 text-sm" isLoading={isLoading}>
              Authenticate <ArrowRight className="ml-2 w-4 h-4" />
            </Button>

            <div className="text-center">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Don't have an account?{' '}
                <Link to="/signup" className="text-black hover:text-accent underline">
                  Sign up
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;