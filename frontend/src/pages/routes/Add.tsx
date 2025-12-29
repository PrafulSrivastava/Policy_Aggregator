/**
 * Add Route Page Component
 * Form to create a new route subscription
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createRoute } from '../../services/routes';
import type { CreateRouteRequest } from '../../services/routes';
import Select from '../../components/forms/Select';
import EmailInput from '../../components/forms/EmailInput';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import { COUNTRIES, VISA_TYPES } from '../../utils/countries';

interface FormErrors {
  originCountry?: string;
  destinationCountry?: string;
  visaType?: string;
  email?: string;
  general?: string;
}

const AddRoute: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<CreateRouteRequest>({
    originCountry: '',
    destinationCountry: '',
    visaType: '',
    email: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.originCountry) {
      newErrors.originCountry = 'Origin country is required';
    } else if (formData.originCountry.length !== 2) {
      newErrors.originCountry = 'Country code must be 2 characters';
    }

    if (!formData.destinationCountry) {
      newErrors.destinationCountry = 'Destination country is required';
    } else if (formData.destinationCountry.length !== 2) {
      newErrors.destinationCountry = 'Country code must be 2 characters';
    }

    if (!formData.visaType) {
      newErrors.visaType = 'Visa type is required';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
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
      // Convert country codes to uppercase (backend expects uppercase)
      const routeData: CreateRouteRequest = {
        ...formData,
        originCountry: formData.originCountry.toUpperCase(),
        destinationCountry: formData.destinationCountry.toUpperCase(),
      };

      const createdRoute = await createRoute(routeData);

      // Success - redirect to routes list
      navigate('/routes', { 
        state: { 
          message: `Route ${createdRoute.origin_country} → ${createdRoute.destination_country} created successfully` 
        } 
      });
    } catch (error) {
      setLoading(false);

      // Handle specific error types
      if (error instanceof Error) {
        const errorWithCode = error as Error & { code?: string; status?: number; details?: { [key: string]: string[] } };

        // Duplicate route error
        if (errorWithCode.code === 'DUPLICATE_ROUTE') {
          setGeneralError('This route already exists. Please choose a different combination.');
          return;
        }

        // Validation errors with field details
        if (errorWithCode.code === 'VALIDATION_ERROR' && errorWithCode.details) {
          const fieldErrors: FormErrors = {};
          
          // Map backend field names to frontend field names
          if (errorWithCode.details.origin_country) {
            fieldErrors.originCountry = errorWithCode.details.origin_country[0];
          }
          if (errorWithCode.details.destination_country) {
            fieldErrors.destinationCountry = errorWithCode.details.destination_country[0];
          }
          if (errorWithCode.details.visa_type) {
            fieldErrors.visaType = errorWithCode.details.visa_type[0];
          }
          if (errorWithCode.details.email) {
            fieldErrors.email = errorWithCode.details.email[0];
          }

          setErrors(fieldErrors);
          return;
        }

        // Other errors
        setGeneralError(error.message || 'Failed to create route. Please try again.');
      } else {
        setGeneralError('An unexpected error occurred. Please try again.');
      }
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: keyof CreateRouteRequest) => (
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

  // Convert countries to select options
  const countryOptions = COUNTRIES.map((country) => ({
    value: country.code,
    label: `${country.code} - ${country.name}`,
  }));

  const visaTypeOptions = VISA_TYPES.map((visa) => ({
    value: visa.value,
    label: visa.label,
  }));

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-7xl font-display font-bold mb-8 tracking-tight">
          Add Route
        </h1>

        {/* General Error Message */}
        {generalError && (
          <div className="mb-6">
            <ErrorMessage message={generalError} />
          </div>
        )}

        {/* Loading State */}
        {loading && <LoadingSpinner message="Creating route..." />}

        {/* Form */}
        {!loading && (
          <div className="card">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Origin Country */}
              <Select
                id="originCountry"
                label="Origin Country"
                required
                options={countryOptions}
                placeholder="Select origin country"
                value={formData.originCountry}
                onChange={handleChange('originCountry')}
                error={errors.originCountry}
                disabled={loading}
              />

              {/* Destination Country */}
              <Select
                id="destinationCountry"
                label="Destination Country"
                required
                options={countryOptions}
                placeholder="Select destination country"
                value={formData.destinationCountry}
                onChange={handleChange('destinationCountry')}
                error={errors.destinationCountry}
                disabled={loading}
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
                disabled={loading}
              />

              {/* Email */}
              <EmailInput
                id="email"
                label="Email"
                required
                value={formData.email}
                onChange={handleChange('email')}
                error={errors.email}
                disabled={loading}
                placeholder="Enter email address"
              />

              {/* Form Actions */}
              <div className="flex items-center space-x-4 pt-4">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading}
                >
                  Create Route
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => navigate('/routes')}
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

export default AddRoute;

