// Data transformation utilities for converting between frontend display format and API format

// Country code mapping
export const COUNTRY_CODES: Record<string, string> = {
  'IN': 'India',
  'DE': 'Germany',
  'US': 'USA',
  'UK': 'United Kingdom',
  'GB': 'United Kingdom', // Alternative code
  'CA': 'Canada',
  'FR': 'France',
  'AU': 'Australia',
  'JP': 'Japan',
  'CN': 'China',
  'BR': 'Brazil',
  'MX': 'Mexico',
  'IT': 'Italy',
  'ES': 'Spain',
  'NL': 'Netherlands',
  'BE': 'Belgium',
  'CH': 'Switzerland',
  'AT': 'Austria',
  'SE': 'Sweden',
  'NO': 'Norway',
  'DK': 'Denmark',
  'FI': 'Finland',
  'PL': 'Poland',
  'IE': 'Ireland',
  'PT': 'Portugal',
  'GR': 'Greece',
  'CZ': 'Czech Republic',
  'HU': 'Hungary',
  'RO': 'Romania',
  'BG': 'Bulgaria',
  'HR': 'Croatia',
  'SK': 'Slovakia',
  'SI': 'Slovenia',
  'EE': 'Estonia',
  'LV': 'Latvia',
  'LT': 'Lithuania',
  'LU': 'Luxembourg',
  'MT': 'Malta',
  'CY': 'Cyprus',
};

export const COUNTRY_NAMES: Record<string, string> = Object.fromEntries(
  Object.entries(COUNTRY_CODES).map(([code, name]) => [name, code])
);

export function getCountryName(code: string): string {
  return COUNTRY_CODES[code.toUpperCase()] || code;
}

export function getCountryCode(name: string): string {
  // Try exact match first
  if (COUNTRY_NAMES[name]) {
    return COUNTRY_NAMES[name];
  }
  // Try case-insensitive match
  const normalizedName = name.toLowerCase();
  for (const [countryName, code] of Object.entries(COUNTRY_NAMES)) {
    if (countryName.toLowerCase() === normalizedName) {
      return code;
    }
  }
  // Fallback: try to extract first 2 uppercase characters
  return name.toUpperCase().slice(0, 2);
}

// Status transformation
export function transformStatus(status: string): 'Healthy' | 'Stale' | 'Error' {
  const normalized = status.toLowerCase();
  if (normalized === 'healthy' || normalized === 'active') return 'Healthy';
  if (normalized === 'stale') return 'Stale';
  if (normalized === 'error' || normalized === 'failed') return 'Error';
  return 'Stale'; // default
}

// Fetch type transformation
export function transformFetchType(type: string): 'HTML' | 'PDF' {
  return type.toUpperCase() === 'PDF' ? 'PDF' : 'HTML';
}

// Check frequency transformation
export function transformCheckFrequency(freq: string): 'Daily' | 'Weekly' | 'Custom' {
  const normalized = freq.toLowerCase();
  if (normalized === 'daily') return 'Daily';
  if (normalized === 'weekly') return 'Weekly';
  return 'Custom';
}

// Format date for display
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'Never';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

// Format date for display (short)
export function formatDateShort(dateString: string | null | undefined): string {
  if (!dateString) return 'Never';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString.split('T')[0];
  }
}

// Get all country options for select
export function getCountryOptions(): Array<{ value: string; label: string }> {
  return Object.entries(COUNTRY_CODES).map(([code, name]) => ({
    value: code,
    label: `${name} (${code})`,
  }));
}

