/**
 * Source Modal Component
 * Modal form for creating and editing sources
 */

import React, { useState, useEffect } from 'react';
import type { Source, CreateSourceRequest, UpdateSourceRequest } from '../../services/sources';
import { createSource, updateSource } from '../../services/sources';
import Modal from '../Modal';
import Input from '../forms/Input';
import Select from '../forms/Select';
import Radio from '../forms/Radio';
import { COUNTRIES, VISA_TYPES } from '../../utils/countries';

interface SourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  source?: Source | null;
}

interface FormErrors {
  name?: string;
  country?: string;
  visaType?: string;
  url?: string;
  fetchType?: string;
  checkFrequency?: string;
}

const SourceModal: React.FC<SourceModalProps> = ({ isOpen, onClose, onSuccess, source }) => {
  const isEditMode = !!source;

  const [formData, setFormData] = useState<CreateSourceRequest>({
    name: '',
    country: '',
    visaType: '',
    url: '',
    fetchType: 'html',
    checkFrequency: 'daily',
    isActive: true,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens/closes or source changes
  useEffect(() => {
    if (isOpen) {
      if (source) {
        // Edit mode: pre-fill form
        setFormData({
          name: source.name,
          country: source.country,
          visaType: source.visa_type,
          url: source.url,
          fetchType: source.fetch_type,
          checkFrequency: source.check_frequency,
          isActive: source.is_active,
        });
      } else {
        // Create mode: reset form
        setFormData({
          name: '',
          country: '',
          visaType: '',
          url: '',
          fetchType: 'html',
          checkFrequency: 'daily',
          isActive: true,
        });
      }
      setErrors({});
      setError(null);
    }
  }, [isOpen, source]);

  /**
   * Validate form data
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.name || formData.name.trim() === '') {
      newErrors.name = 'Name is required';
    }

    if (!formData.country) {
      newErrors.country = 'Region is required';
    }

    if (!formData.visaType) {
      newErrors.visaType = 'Type is required';
    }

    if (!formData.url || formData.url.trim() === '') {
      newErrors.url = 'Endpoint URL is required';
    } else {
      // Basic URL validation
      try {
        new URL(formData.url);
      } catch {
        newErrors.url = 'Invalid URL format';
      }
    }

    if (!formData.fetchType) {
      newErrors.fetchType = 'Fetch Method is required';
    }

    if (!formData.checkFrequency) {
      newErrors.checkFrequency = 'Frequency is required';
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
      if (isEditMode && source) {
        // Update existing source
        const updateData: UpdateSourceRequest = {
          name: formData.name,
          country: formData.country,
          visaType: formData.visaType,
          url: formData.url,
          fetchType: formData.fetchType,
          checkFrequency: formData.checkFrequency,
          isActive: formData.isActive,
        };
        await updateSource(source.id, updateData);
      } else {
        // Create new source
        await createSource(formData);
      }

      // Success - close modal and refresh list
      onSuccess();
      onClose();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save source';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Source' : 'Add Node'}
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-foreground text-background border-2 border-foreground">
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {/* Name */}
        <div>
          <Input
            id="name"
            label="Name"
            type="text"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value });
              if (errors.name) {
                setErrors({ ...errors, name: undefined });
              }
            }}
            error={errors.name}
            required
          />
        </div>

        {/* Region */}
        <div>
          <Select
            id="country"
            label="Region"
            value={formData.country}
            onChange={(e) => {
              setFormData({ ...formData, country: e.target.value });
              if (errors.country) {
                setErrors({ ...errors, country: undefined });
              }
            }}
            error={errors.country}
            required
            options={COUNTRIES.map((c) => ({ value: c.code, label: `${c.code} - ${c.name}` }))}
            placeholder="Select region"
          />
        </div>

        {/* Type (Visa Type) */}
        <div>
          <Select
            id="visaType"
            label="Type"
            value={formData.visaType}
            onChange={(e) => {
              setFormData({ ...formData, visaType: e.target.value });
              if (errors.visaType) {
                setErrors({ ...errors, visaType: undefined });
              }
            }}
            error={errors.visaType}
            required
            options={VISA_TYPES.map((vt) => ({ value: vt.value, label: vt.label }))}
            placeholder="Select visa type"
          />
        </div>

        {/* Endpoint URL */}
        <div>
          <Input
            id="url"
            label="Endpoint URL"
            type="url"
            value={formData.url}
            onChange={(e) => {
              setFormData({ ...formData, url: e.target.value });
              if (errors.url) {
                setErrors({ ...errors, url: undefined });
              }
            }}
            error={errors.url}
            required
          />
        </div>

        {/* Fetch Method */}
        <div>
          <Radio
            name="fetchType"
            label="Fetch Method"
            value={formData.fetchType}
            onChange={(value) => {
              setFormData({ ...formData, fetchType: value as 'html' | 'pdf' });
              if (errors.fetchType) {
                setErrors({ ...errors, fetchType: undefined });
              }
            }}
            error={errors.fetchType}
            required
            options={[
              { value: 'html', label: 'HTML' },
              { value: 'pdf', label: 'PDF' },
            ]}
          />
        </div>

        {/* Frequency */}
        <div>
          <Select
            id="checkFrequency"
            label="Frequency"
            value={formData.checkFrequency}
            onChange={(e) => {
              setFormData({ ...formData, checkFrequency: e.target.value as 'daily' | 'weekly' | 'custom' });
              if (errors.checkFrequency) {
                setErrors({ ...errors, checkFrequency: undefined });
              }
            }}
            error={errors.checkFrequency}
            required
            options={[
              { value: 'daily', label: 'Daily' },
              { value: 'weekly', label: 'Weekly' },
              { value: 'custom', label: 'Custom' },
            ]}
            placeholder="Select frequency"
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
            {loading ? 'Saving...' : isEditMode ? 'Update' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default SourceModal;

