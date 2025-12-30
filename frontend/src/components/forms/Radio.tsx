/**
 * Radio Component
 * Reusable radio button group with error state support
 */

import React from 'react';

interface RadioOption {
  value: string;
  label: string;
}

interface RadioProps {
  name: string;
  label?: string;
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  error?: string;
  required?: boolean;
  className?: string;
}

const Radio: React.FC<RadioProps> = ({
  name,
  label,
  options,
  value,
  onChange,
  error,
  required = false,
  className = '',
}) => {
  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium mb-2 uppercase tracking-widest">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="space-y-2">
        {options.map((option) => (
          <label
            key={option.value}
            className="flex items-center cursor-pointer"
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange(e.target.value)}
              className="mr-2 w-4 h-4 border-2 border-foreground accent-foreground"
              aria-invalid={error ? 'true' : 'false'}
            />
            <span className="text-sm font-body">{option.label}</span>
          </label>
        ))}
      </div>
      {error && (
        <p
          id={`${name}-error`}
          className="mt-1 text-sm text-red-500"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default Radio;


