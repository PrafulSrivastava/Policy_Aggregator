import React, { useState } from 'react';
import { Button, Card, Input } from '../components/Common';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  console.log('[LOGIN] Login page component rendering...');
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

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

            <Button type="submit" className="w-full h-16 text-sm" isLoading={isLoading}>
              Authenticate <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;