/**
 * Route Modal Component
 * Modal form for creating and editing routes
 */

import React, { useState, useEffect } from 'react';
import type { RouteSubscription, CreateRouteRequest } from '../../services/routes';
import { createRoute, updateRoute } from '../../services/routes';
import Modal from '../Modal';
import Select from '../forms/Select';
import { COUNTRIES, VISA_TYPES } from '../../utils/countries';

interface RouteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  route?: RouteSubscription | null;
}

interface FormErrors {
  originCountry?: string;
  destinationCountry?: string;
  visaType?: string;
}

const RouteModal: React.FC<RouteModalProps> = ({ isOpen, onClose, onSuccess, route }) => {
  const isEditMode = !!route;

  const [formData, setFormData] = useState<CreateRouteRequest>({
    originCountry: '',
    destinationCountry: '',
    visaType: '',
    email: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens/closes or route changes
  useEffect(() => {
    if (isOpen) {
      if (route) {
        // Edit mode: pre-fill form
        setFormData({
          originCountry: route.origin_country,
          destinationCountry: route.destination_country,
          visaType: route.visa_type,
          email: route.email,
        });
      } else {
        // Create mode: reset form
        setFormData({
          originCountry: '',
          destinationCountry: '',
          visaType: '',
          email: '',
        });
      }
      setErrors({});
      setError(null);
    }
  }, [isOpen, route]);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.originCountry) {
      newErrors.originCountry = 'Origin Node is required';
    }

    if (!formData.destinationCountry) {
      newErrors.destinationCountry = 'Destination Node is required';
    }

    if (!formData.visaType) {
      newErrors.visaType = 'Visa Classification is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Convert country codes to uppercase
      const routeData: CreateRouteRequest = {
        ...formData,
        originCountry: formData.originCountry.toUpperCase(),
        destinationCountry: formData.destinationCountry.toUpperCase(),
      };

      if (isEditMode && route) {
        // Update existing route
        await updateRoute(route.id, routeData);
      } else {
        // Create new route
        await createRoute(routeData);
      }

      // Success - close modal and refresh list
      onSuccess();
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save route';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Route' : 'Initialize Route'}
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-foreground text-background border-2 border-foreground">
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {/* Origin Node */}
        <div>
          <label htmlFor="originCountry" className="block text-sm font-medium mb-2 uppercase tracking-widest">
            Origin Node
          </label>
          <Select
            id="originCountry"
            value={formData.originCountry}
            onChange={(e) => {
              setFormData({ ...formData, originCountry: e.target.value });
              if (errors.originCountry) {
                setErrors({ ...errors, originCountry: undefined });
              }
            }}
            error={errors.originCountry}
            required
            options={[
              { value: '', label: 'Select origin country' },
              ...COUNTRIES.map((country) => ({
                value: country.code,
                label: `${country.code} - ${country.name}`,
              })),
            ]}
          />
        </div>

        {/* Destination Node */}
        <div>
          <label htmlFor="destinationCountry" className="block text-sm font-medium mb-2 uppercase tracking-widest">
            Destination Node
          </label>
          <Select
            id="destinationCountry"
            value={formData.destinationCountry}
            onChange={(e) => {
              setFormData({ ...formData, destinationCountry: e.target.value });
              if (errors.destinationCountry) {
                setErrors({ ...errors, destinationCountry: undefined });
              }
            }}
            error={errors.destinationCountry}
            required
            options={[
              { value: '', label: 'Select destination country' },
              ...COUNTRIES.map((country) => ({
                value: country.code,
                label: `${country.code} - ${country.name}`,
              })),
            ]}
          />
        </div>

        {/* Visa Classification */}
        <div>
          <label htmlFor="visaType" className="block text-sm font-medium mb-2 uppercase tracking-widest">
            Visa Classification
          </label>
          <Select
            id="visaType"
            value={formData.visaType}
            onChange={(e) => {
              setFormData({ ...formData, visaType: e.target.value });
              if (errors.visaType) {
                setErrors({ ...errors, visaType: undefined });
              }
            }}
            error={errors.visaType}
            required
            options={[
              { value: '', label: 'Select visa type' },
              ...VISA_TYPES,
            ]}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4 pt-4 border-t-2 border-foreground">
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Confirm Sequence'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default RouteModal;

