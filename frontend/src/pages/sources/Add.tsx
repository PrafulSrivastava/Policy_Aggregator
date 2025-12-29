/**
 * Add Source Page Component
 * Form to create a new source
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { createSource, addSourceToRoute } from '../../services/sources';
import type { CreateSourceRequest } from '../../services/sources';
import Input from '../../components/forms/Input';
import Select from '../../components/forms/Select';
import Radio from '../../components/forms/Radio';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import { COUNTRIES, VISA_TYPES } from '../../utils/countries';
import type { RouteSubscription } from '../../services/routes';

interface FormErrors {
  country?: string;
  visaType?: string;
  url?: string;
  name?: string;
  fetchType?: string;
  checkFrequency?: string;
  general?: string;
}

const AddSource: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Check if we're adding from a route context
  const routeContext = location.state?.route as RouteSubscription | undefined;
  const routeId = routeContext?.id;

  const [formData, setFormData] = useState<CreateSourceRequest>({
    country: routeContext?.destination_country || '',
    visaType: routeContext?.visa_type || '',
    url: '',
    name: '',
    fetchType: 'html',
    checkFrequency: 'daily',
    isActive: true,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  /**
   * Validate URL format
   */
  const validateUrl = (url: string): boolean => {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.country) {
      newErrors.country = 'Country is required';
    } else if (formData.country.length !== 2) {
      newErrors.country = 'Country code must be 2 characters';
    }

    if (!formData.visaType) {
      newErrors.visaType = 'Visa type is required';
    }

    if (!formData.url) {
      newErrors.url = 'URL is required';
    } else if (!validateUrl(formData.url)) {
      newErrors.url = 'Please enter a valid URL (must start with http:// or https://)';
    }

    if (!formData.name) {
      newErrors.name = 'Source name is required';
    }

    if (!formData.fetchType) {
      newErrors.fetchType = 'Fetch type is required';
    } else if (!['html', 'pdf'].includes(formData.fetchType)) {
      newErrors.fetchType = 'Fetch type must be HTML or PDF';
    }

    if (!formData.checkFrequency) {
      newErrors.checkFrequency = 'Check frequency is required';
    } else if (!['daily', 'weekly', 'custom'].includes(formData.checkFrequency)) {
      newErrors.checkFrequency = 'Check frequency must be daily, weekly, or custom';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});
    setGeneralError(null);

    // Validate form
    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      let createdSource;

      // If we have a route context, use addSourceToRoute
      if (routeId) {
        createdSource = await addSourceToRoute(routeId, formData);
      } else {
        createdSource = await createSource(formData);
      }

      // Success - redirect based on context
      if (routeId && routeContext) {
        // Redirect back to route detail or routes list
        navigate(`/routes/${routeId}`, {
          state: {
            message: `Source "${createdSource.name}" added successfully`,
          },
        });
      } else {
        // Redirect to sources list
        navigate('/sources', {
          state: {
            message: `Source "${createdSource.name}" created successfully`,
          },
        });
      }
    } catch (error) {
      setLoading(false);

      // Handle specific error types
      if (error instanceof Error) {
        const errorWithCode = error as Error & { code?: string; status?: number; details?: { [key: string]: string[] } };

        // Duplicate source error
        if (errorWithCode.code === 'DUPLICATE_SOURCE') {
          setGeneralError('This source already exists. Please check the URL, country, and visa type combination.');
          return;
        }

        // Validation errors with field details
        if (errorWithCode.code === 'VALIDATION_ERROR' && errorWithCode.details) {
          const fieldErrors: FormErrors = {};
          
          // Map backend field names to frontend field names
          if (errorWithCode.details.country) {
            fieldErrors.country = errorWithCode.details.country[0];
          }
          if (errorWithCode.details.visa_type) {
            fieldErrors.visaType = errorWithCode.details.visa_type[0];
          }
          if (errorWithCode.details.url) {
            fieldErrors.url = errorWithCode.details.url[0];
          }
          if (errorWithCode.details.name) {
            fieldErrors.name = errorWithCode.details.name[0];
          }
          if (errorWithCode.details.fetch_type) {
            fieldErrors.fetchType = errorWithCode.details.fetch_type[0];
          }
          if (errorWithCode.details.check_frequency) {
            fieldErrors.checkFrequency = errorWithCode.details.check_frequency[0];
          }

          setErrors(fieldErrors);
          return;
        }

        // Other errors
        setGeneralError(error.message || 'Failed to create source. Please try again.');
      } else {
        setGeneralError('An unexpected error occurred. Please try again.');
      }
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof CreateSourceRequest) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ): void => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value,
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  /**
   * Handle radio change
   */
  const handleRadioChange = (field: 'fetchType' | 'checkFrequency') => (
    value: string
  ): void => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  // Convert countries to select options
  const countryOptions = COUNTRIES.map((country) => ({
    value: country.code,
    label: `${country.code} - ${country.name}`,
  }));

  const visaTypeOptions = VISA_TYPES.map((visa) => ({
    value: visa.value,
    label: visa.label,
  }));

  const fetchTypeOptions = [
    { value: 'html', label: 'HTML' },
    { value: 'pdf', label: 'PDF' },
  ];

  const checkFrequencyOptions = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'custom', label: 'Custom' },
  ];

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-7xl font-display font-bold mb-8 tracking-tight">
          {routeContext ? 'Add Source to Route' : 'Add Source'}
        </h1>

        {routeContext && (
          <div className="mb-6 p-4 bg-muted border-2 border-foreground">
            <p className="text-sm font-medium mb-1">Adding source for route:</p>
            <p className="text-lg font-body">
              {routeContext.origin_country} → {routeContext.destination_country} ({routeContext.visa_type})
            </p>
          </div>
        )}

        {/* General Error Message */}
        {generalError && (
          <div className="mb-6">
            <ErrorMessage message={generalError} />
          </div>
        )}

        {/* Loading State */}
        {loading && <LoadingSpinner message="Creating source..." />}

        {/* Form */}
        {!loading && (
          <div className="card">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Country */}
              <Select
                id="country"
                label="Country"
                required
                options={countryOptions}
                placeholder="Select country"
                value={formData.country}
                onChange={handleChange('country')}
                error={errors.country}
                disabled={loading || !!routeContext}
              />

              {/* Visa Type */}
              <Select
                id="visaType"
                label="Visa Type"
                required
                options={visaTypeOptions}
                placeholder="Select visa type"
                value={formData.visaType}
                onChange={handleChange('visaType')}
                error={errors.visaType}
                disabled={loading || !!routeContext}
              />

              {/* Source URL */}
              <Input
                id="url"
                type="url"
                label="Source URL"
                required
                value={formData.url}
                onChange={handleChange('url')}
                error={errors.url}
                disabled={loading}
                placeholder="https://example.com/policy"
              />

              {/* Source Name */}
              <Input
                id="name"
                type="text"
                label="Source Name"
                required
                value={formData.name}
                onChange={handleChange('name')}
                error={errors.name}
                disabled={loading}
                placeholder="Enter a descriptive name for this source"
              />

              {/* Fetch Type */}
              <Radio
                name="fetchType"
                label="Fetch Type"
                required
                options={fetchTypeOptions}
                value={formData.fetchType}
                onChange={handleRadioChange('fetchType')}
                error={errors.fetchType}
              />

              {/* Check Frequency */}
              <Select
                id="checkFrequency"
                label="Check Frequency"
                required
                options={checkFrequencyOptions}
                placeholder="Select check frequency"
                value={formData.checkFrequency}
                onChange={handleChange('checkFrequency')}
                error={errors.checkFrequency}
                disabled={loading}
              />

              {/* Form Actions */}
              <div className="flex items-center space-x-4 pt-4">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading}
                >
                  Create Source
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    if (routeId) {
                      navigate(`/routes/${routeId}`);
                    } else {
                      navigate('/sources');
                    }
                  }}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default AddSource;

