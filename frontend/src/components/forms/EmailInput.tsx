/**
 * EmailInput Component
 * Email input with built-in validation
 */

import React from 'react';
import Input from './Input';

interface EmailInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  error?: string;
  required?: boolean;
}

/**
 * Validate email format
 */
const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const EmailInput: React.FC<EmailInputProps> = ({
  label = 'Email',
  error,
  required = false,
  value,
  onChange,
  onBlur,
  ...props
}) => {
  const [localError, setLocalError] = React.useState<string | undefined>(error);
  const [touched, setTouched] = React.useState(false);

  // Sync external error prop
  React.useEffect(() => {
    setLocalError(error);
  }, [error]);

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setTouched(true);
    
    // Client-side validation
    if (required && !value) {
      setLocalError('Email is required');
    } else if (value && typeof value === 'string' && !validateEmail(value)) {
      setLocalError('Please enter a valid email address');
    } else {
      setLocalError(undefined);
    }

    onBlur?.(e);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Clear error when user starts typing
    if (touched && localError) {
      const newValue = e.target.value;
      if (newValue && validateEmail(newValue)) {
        setLocalError(undefined);
      } else if (newValue && !validateEmail(newValue)) {
        setLocalError('Please enter a valid email address');
      }
    }

    onChange?.(e);
  };

  return (
    <Input
      {...props}
      type="email"
      label={label}
      error={localError}
      required={required}
      value={value}
      onChange={handleChange}
      onBlur={handleBlur}
      autoComplete="email"
    />
  );
};

export default EmailInput;


