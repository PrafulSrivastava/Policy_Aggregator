import React from 'react';
import { NavLink } from 'react-router-dom';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Check, AlertTriangle, X, LogOut, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// Utility for merging tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Button - Swiss Style: Rectangular, Bold, Uppercase
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, variant = 'primary', size = 'md', isLoading, className, disabled, ...props 
}) => {
  const baseStyles = "inline-flex items-center justify-center font-bold uppercase tracking-wider transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none rounded-none border-2";
  
  const variants = {
    // Solid Black, inverts to Red/White or White/Red on hover
    primary: "bg-black text-white border-black hover:bg-accent hover:border-accent hover:text-white",
    // White with Black border
    secondary: "bg-white text-black border-black hover:bg-black hover:text-white",
    // Red with Red border
    danger: "bg-white text-accent border-accent hover:bg-accent hover:text-white",
    // No border, text only
    ghost: "border-transparent text-black hover:bg-muted"
  };

  const sizes = {
    sm: "h-8 px-4 text-[10px]",
    md: "h-12 px-6 text-xs",
    lg: "h-16 px-10 text-sm"
  };

  return (
    <button 
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="mr-2 animate-spin rounded-full h-3 w-3 border-b-2 border-current"></span>
      ) : null}
      {children}
    </button>
  );
};

// Card - Swiss Style: Thick borders, no rounding, visible structure
export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={cn("bg-white border-2 border-black p-0 shadow-none rounded-none", className)}>
    {children}
  </div>
);

// Badge - Swiss Style: Rectangular, High Contrast
interface BadgeProps {
  status: 'Healthy' | 'Stale' | 'Error' | 'Success' | 'Warning' | 'Neutral' | 'High' | 'Medium' | 'Low';
  text?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, text }) => {
  // Map statuses to visual styles
  // Healthy/Success/Low = Black/White (Objective)
  // Warning/Medium = Outline or Muted
  // Error/High = Red (Signal)
  
  const styles = {
    Healthy: "bg-black text-white border-black",
    Success: "bg-black text-white border-black",
    Stale: "bg-white text-black border-black border-dashed",
    Warning: "bg-white text-black border-black border-dashed",
    Error: "bg-accent text-white border-accent",
    Neutral: "bg-muted text-black border-muted",
    High: "bg-accent text-white border-accent",
    Medium: "bg-black text-white border-black",
    Low: "bg-white text-black border-black",
  };

  const icons = {
    Healthy: <Check className="w-3 h-3 mr-1.5" />,
    Success: <Check className="w-3 h-3 mr-1.5" />,
    Stale: <AlertTriangle className="w-3 h-3 mr-1.5" />,
    Warning: <AlertTriangle className="w-3 h-3 mr-1.5" />,
    Error: <AlertTriangle className="w-3 h-3 mr-1.5" />,
    Neutral: null,
    High: <ArrowRight className="w-3 h-3 mr-1.5 -rotate-45" />,
    Medium: <ArrowRight className="w-3 h-3 mr-1.5" />,
    Low: <ArrowRight className="w-3 h-3 mr-1.5 rotate-45" />,
  };

  return (
    <span className={cn("inline-flex items-center px-2 py-1 text-[10px] font-bold uppercase tracking-widest border-2 rounded-none", styles[status])}>
      {icons[status]}
      {text || status}
    </span>
  );
};

// Input - Swiss Style: Thick border, boxy
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, className, id, ...props }) => (
  <div className="w-full">
    {label && <label htmlFor={id} className="block text-xs font-bold uppercase tracking-wider text-black mb-2">{label}</label>}
    <input
      id={id}
      className={cn(
        "flex h-12 w-full rounded-none border-2 border-black bg-white px-4 py-2 text-sm text-black placeholder:text-slate-400 focus:outline-none focus:border-accent focus:ring-0 disabled:cursor-not-allowed disabled:bg-muted disabled:text-slate-500 transition-colors duration-150",
        error && "border-accent text-accent",
        className
      )}
      {...props}
    />
    {error && <p className="mt-1 text-xs text-accent font-bold uppercase">{error}</p>}
  </div>
);

// Select - Swiss Style
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select: React.FC<SelectProps> = ({ label, error, options, className, id, ...props }) => (
  <div className="w-full">
    {label && <label htmlFor={id} className="block text-xs font-bold uppercase tracking-wider text-black mb-2">{label}</label>}
    <div className="relative">
      <select
        id={id}
        className={cn(
          "flex h-12 w-full appearance-none rounded-none border-2 border-black bg-white px-4 py-2 text-sm font-medium focus:outline-none focus:border-accent focus:ring-0 disabled:cursor-not-allowed disabled:bg-muted",
          error && "border-accent text-accent",
          className
        )}
        {...props}
      >
        <option value="">SELECT...</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-black">
        <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
      </div>
    </div>
    {error && <p className="mt-1 text-xs text-accent font-bold uppercase">{error}</p>}
  </div>
);

// Modal - Swiss Style: Strict rectangle, visible boundaries
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'md' | 'lg';
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer, size = 'md' }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-white/90 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className={cn(
          "bg-white border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] w-full max-h-[90vh] overflow-y-auto flex flex-col rounded-none",
          size === 'md' ? 'max-w-md' : 'max-w-2xl'
        )}
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-black bg-muted">
          <h3 className="text-sm font-black uppercase tracking-widest text-black">{title}</h3>
          <button onClick={onClose} className="text-black hover:text-accent transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="p-8">
          {children}
        </div>
        {footer && (
          <div className="flex items-center justify-end px-6 py-6 bg-white border-t-2 border-black gap-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// Navbar - Swiss Style: Brutalist, high structure
export const Navbar: React.FC = () => {
  console.log('[NAVBAR] Navbar component rendering...');
  const { logout } = useAuth();
  
  const links = [
    { to: '/', label: 'Dashboard' },
    { to: '/routes', label: 'Subscriptions' },
    { to: '/sources', label: 'Sources' },
    { to: '/changes', label: 'History' },
    { to: '/trigger', label: 'Trigger' },
    { to: '/settings', label: 'Settings' },
  ];

  return (
    <nav className="bg-white border-b-4 border-black sticky top-0 z-40">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-black text-2xl font-black uppercase tracking-tighter leading-none">
                Policy<br/><span className="text-accent">Aggregator</span>
              </span>
            </div>
            <div className="hidden sm:ml-12 sm:flex sm:space-x-8">
              {links.map((link, idx) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    cn(
                      "inline-flex items-center px-1 pt-1 border-b-4 text-xs font-bold uppercase tracking-wider transition-all h-full mt-1",
                      isActive
                        ? "border-accent text-black"
                        : "border-transparent text-slate-500 hover:text-black hover:border-slate-300"
                    )
                  }
                >
                  <span className="text-accent mr-1 text-[10px]">0{idx + 1}.</span> {link.label}
                </NavLink>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center">
              <div className="h-10 w-10 border-2 border-black bg-muted flex items-center justify-center text-black text-xs font-bold">
                AD
              </div>
            </div>
            <button 
              onClick={logout}
              className="text-xs font-bold uppercase tracking-wider text-black hover:text-accent flex items-center transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Layout - Swiss Style: Grid background
export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  console.log('[LAYOUT] Layout component rendering with children');
  return (
    <div className="min-h-screen bg-swiss-grid">
      <Navbar />
      <main className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {children}
      </main>
    </div>
  );
};