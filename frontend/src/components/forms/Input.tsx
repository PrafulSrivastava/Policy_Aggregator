/**
 * Input Component
 * Reusable text input with error state support
 */

import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  required?: boolean;
}

const Input: React.FC<InputProps> = ({
  label,
  error,
  required = false,
  className = '',
  ...props
}) => {
  const inputClasses = `input ${error ? 'border-red-500' : ''} ${className}`;

  return (
    <div>
      {label && (
        <label
          htmlFor={props.id}
          className="block text-sm font-medium mb-2 uppercase tracking-widest"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        {...props}
        className={inputClasses}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={error ? `${props.id}-error` : undefined}
      />
      {error && (
        <p
          id={`${props.id}-error`}
          className="mt-1 text-sm text-red-500"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;

