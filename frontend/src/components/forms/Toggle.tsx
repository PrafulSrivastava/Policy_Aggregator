/**
 * Toggle Component
 * Reusable toggle switch with design system styling
 */

import React from 'react';

interface ToggleProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  description?: string;
  className?: string;
}

const Toggle: React.FC<ToggleProps> = ({
  id,
  label,
  checked,
  onChange,
  disabled = false,
  description,
  className = '',
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    if (!disabled) {
      onChange(e.target.checked);
    }
  };

  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <label
            htmlFor={id}
            className={`block text-sm font-medium uppercase tracking-widest ${
              disabled ? 'text-mutedForeground cursor-not-allowed' : 'cursor-pointer'
            }`}
          >
            {label}
          </label>
          {description && (
            <p className="mt-1 text-sm text-mutedForeground font-body normal-case">
              {description}
            </p>
          )}
        </div>
        <div className="ml-4">
          <button
            type="button"
            role="switch"
            aria-checked={checked}
            aria-labelledby={id}
            disabled={disabled}
            onClick={() => !disabled && onChange(!checked)}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-none border-2 border-foreground
              transition-colors duration-instant
              focus:outline-none focus:ring-2 focus:ring-foreground focus:ring-offset-2
              ${checked ? 'bg-foreground' : 'bg-background'}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <span
              className={`
                inline-block h-4 w-4 transform border-2 border-foreground bg-background
                transition-transform duration-instant
                ${checked ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </button>
        </div>
      </div>
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={handleChange}
        disabled={disabled}
        className="sr-only"
        aria-hidden="true"
      />
    </div>
  );
};

export default Toggle;

