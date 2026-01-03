import React, { useState } from 'react';
import { Button, Card, Input } from '../components/Common';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Signup: React.FC = () => {
  console.log('[SIGNUP] Signup page component rendering...');
  const { signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  const validateEmail = (email: string): string | null => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      return 'Email is required';
    }
    if (!emailRegex.test(email)) {
      return 'Invalid email format';
    }
    return null;
  };

  const validatePassword = (password: string): string | null => {
    if (!password) {
      return 'Password is required';
    }
    if (password.length < 8) {
      return 'Password must be at least 8 characters';
    }
    return null;
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    const emailError = validateEmail(email);
    if (emailError) errors.email = emailError;
    
    const passwordError = validatePassword(password);
    if (passwordError) errors.password = passwordError;
    
    if (!confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (!termsAccepted) {
      errors.terms = 'You must accept the terms and conditions';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('[SIGNUP] Form submitted with email:', email);
    setError('');
    setFieldErrors({});

    if (!validateForm()) {
      console.log('[SIGNUP] Form validation failed');
      return;
    }

    setIsLoading(true);

    try {
      console.log('[SIGNUP] Calling signup function...');
      await signup(email, password);
      console.log('[SIGNUP] ✅ Signup successful, navigating to dashboard...');
      navigate('/');
    } catch (err: any) {
      console.error('[SIGNUP] ❌ Signup failed:', err);
      const errorMessage = err.response?.data?.detail || 'Signup failed. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      console.log('[SIGNUP] Signup attempt completed');
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
            <p className="text-xl font-bold uppercase tracking-wide">Create Account</p>
            <p className="text-sm font-medium text-slate-600 max-w-md">
              Join Policy Aggregator to monitor global migration policies and receive automated change notifications.
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
            <h2 className="text-4xl font-black uppercase tracking-tight mb-2">Account Creation</h2>
            <div className="h-1 w-24 bg-accent"></div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-8">
            <Input
              id="email"
              type="email"
              label="Email Address"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) {
                  setFieldErrors({ ...fieldErrors, email: '' });
                }
              }}
              placeholder="user@example.com"
              autoFocus
              required
              error={fieldErrors.email}
              className="bg-muted focus:bg-white"
            />
            
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                label="Password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (fieldErrors.password) {
                    setFieldErrors({ ...fieldErrors, password: '' });
                  }
                }}
                required
                error={fieldErrors.password}
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

            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                label="Confirm Password"
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (fieldErrors.confirmPassword) {
                    setFieldErrors({ ...fieldErrors, confirmPassword: '' });
                  }
                }}
                required
                error={fieldErrors.confirmPassword}
                className="bg-muted focus:bg-white"
              />
              <button
                type="button"
                className="absolute right-4 top-[2.2rem] text-black hover:text-accent transition-colors"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <div className="flex items-start">
              <input
                id="terms"
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => {
                  setTermsAccepted(e.target.checked);
                  if (fieldErrors.terms) {
                    setFieldErrors({ ...fieldErrors, terms: '' });
                  }
                }}
                className="h-5 w-5 mt-1 text-black focus:ring-accent border-2 border-black rounded-none"
                required
              />
              <label htmlFor="terms" className="ml-3 block text-xs font-bold uppercase tracking-wider text-black">
                I accept the terms and conditions
              </label>
            </div>
            {fieldErrors.terms && (
              <p className="text-xs text-accent font-bold uppercase -mt-6">{fieldErrors.terms}</p>
            )}

            {error && (
              <div className="bg-accent text-white p-4 border-2 border-black flex items-center text-sm font-bold">
                <Lock className="w-4 h-4 mr-3" />
                {error.toUpperCase()}
              </div>
            )}

            <Button type="submit" className="w-full h-16 text-sm" isLoading={isLoading}>
              Create Account <ArrowRight className="ml-2 w-4 h-4" />
            </Button>

            <div className="text-center">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Already have an account?{' '}
                <Link to="/login" className="text-black hover:text-accent underline">
                  Sign in
                </Link>
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Signup;

