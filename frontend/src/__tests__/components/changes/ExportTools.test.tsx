/**
 * Export Tools Component Tests
 * Tests export tools component functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ExportTools from '../../../components/changes/ExportTools';
import type { PolicyChangeDetail } from '../../../services/changes';

// Mock URL.createObjectURL and document.createElement
const mockCreateElement = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();
const mockClick = vi.fn();
const mockRevokeObjectURL = vi.fn();

describe('ExportTools', () => {
  const mockChange: PolicyChangeDetail = {
    id: 'change-1',
    detected_at: '2025-01-27T10:00:00Z',
    summary: 'Policy content updated',
    is_new: true,
    diff_length: 250,
    diff: 'Sample diff text',
    source: {
      id: 'source-1',
      name: 'Germany Student Visa Source',
      url: 'https://example.com/policy',
      country: 'DE',
      visa_type: 'Student',
    },
    route: {
      id: 'route-1',
      origin_country: 'IN',
      destination_country: 'DE',
      visa_type: 'Student',
      display: 'IN → DE, Student',
    },
    old_version: null,
    new_version: {
      id: 'version-1',
      content_hash: 'hash1',
      raw_text: 'New content',
      fetched_at: '2025-01-27T10:00:00Z',
      content_length: 100,
    },
    previous_change_id: null,
    next_change_id: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock document.createElement
    const mockLink = {
      href: '',
      download: '',
      click: mockClick,
    };
    
    mockCreateElement.mockReturnValue(mockLink as any);
    
    window.document.createElement = mockCreateElement as any;
    window.document.body.appendChild = mockAppendChild as any;
    window.document.body.removeChild = mockRemoveChild as any;
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    window.URL.revokeObjectURL = mockRevokeObjectURL;
    window.open = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render export tools section', () => {
    render(<ExportTools change={mockChange} />);

    expect(screen.getByText(/Export Tools/i)).toBeInTheDocument();
    expect(screen.getByText(/Source Link/i)).toBeInTheDocument();
    expect(screen.getByText(/Export JSON/i)).toBeInTheDocument();
  });

  it('should open source URL in new tab when Source Link is clicked', () => {
    render(<ExportTools change={mockChange} />);

    const sourceLinkButton = screen.getByText(/Source Link/i);
    fireEvent.click(sourceLinkButton);

    expect(window.open).toHaveBeenCalledWith(
      'https://example.com/policy',
      '_blank',
      'noopener,noreferrer'
    );
  });

  it('should disable Source Link button when URL is not available', () => {
    const changeWithoutUrl: PolicyChangeDetail = {
      ...mockChange,
      source: {
        ...mockChange.source,
        url: '',
      },
    };

    render(<ExportTools change={changeWithoutUrl} />);

    const sourceLinkButton = screen.getByText(/Source Link/i);
    expect(sourceLinkButton).toBeDisabled();
  });

  it('should export JSON when Export JSON button is clicked', () => {
    const blobSpy = vi.spyOn(window, 'Blob');
    
    render(<ExportTools change={mockChange} />);

    const exportButton = screen.getByText(/Export JSON/i);
    fireEvent.click(exportButton);

    expect(blobSpy).toHaveBeenCalled();
    expect(mockCreateElement).toHaveBeenCalledWith('a');
    expect(mockClick).toHaveBeenCalled();
  });

  it('should include all change data in JSON export', () => {
    const blobSpy = vi.spyOn(window, 'Blob');
    
    render(<ExportTools change={mockChange} />);

    const exportButton = screen.getByText(/Export JSON/i);
    fireEvent.click(exportButton);

    expect(blobSpy).toHaveBeenCalled();
    const blobCall = blobSpy.mock.calls[0];
    expect(blobCall).toBeDefined();
    expect(blobCall?.[0]).toBeDefined();
    expect(Array.isArray(blobCall?.[0])).toBe(true);
    
    if (blobCall && blobCall[0] && Array.isArray(blobCall[0])) {
      const jsonString = blobCall[0][0] as string;
      const exportedData = JSON.parse(jsonString);
      
      expect(exportedData.id).toBe('change-1');
      expect(exportedData.source.name).toBe('Germany Student Visa Source');
      expect(exportedData.route).toBeTruthy();
      expect(exportedData.diff).toBe('Sample diff text');
    }
  });
});

