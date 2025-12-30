# Frontend Analysis & Integration Guide

## Overview

This document analyzes the new React frontend and provides a roadmap for integrating it with the FastAPI backend.

## Technology Stack

### Current Stack
- **Framework:** React 19.2.3 with TypeScript
- **Build Tool:** Vite 6.2.0
- **Routing:** React Router DOM 7.11.0 (HashRouter)
- **Styling:** Tailwind CSS (via `tailwind-merge` and `clsx`)
- **Icons:** Lucide React
- **State Management:** React Context API (AuthContext)

### Development Server
- Port: 3000
- Host: 0.0.0.0

## Project Structure

```
frontend/
├── components/
│   └── Common.tsx          # Reusable UI components (Button, Card, Badge, Input, Select, Modal, Navbar, Layout)
├── context/
│   └── AuthContext.tsx     # Authentication state management
├── pages/
│   ├── Login.tsx           # Login page
│   ├── Dashboard.tsx       # Dashboard with stats and recent changes
│   ├── RouteSubscriptions.tsx  # Route subscription management
│   ├── SourceConfiguration.tsx # Source management
│   ├── ChangeHistory.tsx   # Policy changes list
│   ├── ChangeDetail.tsx    # Individual change detail view
│   ├── ManualTrigger.tsx   # Manual source fetch trigger
│   └── Settings.tsx         # Settings page
├── App.tsx                 # Main app component with routing
├── types.ts                 # TypeScript type definitions
├── data.ts                  # Mock data
└── vite.config.ts          # Vite configuration
```

## Current Implementation Status

### ✅ Completed
- UI components with Swiss/Brutalist design style
- Page structure and routing
- Authentication context (mock)
- Mock data for all entities

### ❌ Missing/Incomplete
- **API Integration:** All data is mocked, no API calls
- **Authentication:** Mock login, no real JWT token handling
- **Type Mismatches:** Frontend types don't match backend API
- **Environment Configuration:** No API base URL configuration
- **Error Handling:** No API error handling
- **Loading States:** Limited loading state management

## Critical Issues & Mismatches

### 1. Type Definitions Mismatch

**Frontend Types (types.ts):**
```typescript
interface RouteSubscription {
  id: number;  // ❌ Should be string (UUID)
  originCountry: string;  // ❌ Should be origin_country (snake_case)
  destinationCountry: string;  // ❌ Should be destination_country
  visaType: string;  // ❌ Should be visa_type
  // Missing: email, is_active, created_at, updated_at
}
```

**Backend API Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",  // UUID string
  "origin_country": "IN",  // 2-char country code
  "destination_country": "DE",
  "visa_type": "Student",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

### 2. Authentication Implementation

**Current (Mock):**
```typescript
// AuthContext.tsx - Mock implementation
const login = () => {
  localStorage.setItem('auth_token', 'mock_token_' + Date.now());
  setIsAuthenticated(true);
};
```

**Required:**
- Real API call to `/auth/login`
- JWT token storage and management
- Token expiration handling
- Automatic token refresh
- Logout API call

### 3. Data Format Mismatches

| Frontend | Backend API |
|----------|------------|
| `id: number` | `id: string` (UUID) |
| `originCountry: "India"` | `origin_country: "IN"` (2-char code) |
| `visaType: "Student"` | `visa_type: "Student"` |
| `fetchType: "HTML"` | `fetch_type: "html"` (lowercase) |
| `checkFrequency: "Daily"` | `check_frequency: "daily"` (lowercase) |
| `status: "Healthy"` | `status: "healthy"` (lowercase) |

### 4. Missing API Integration Layer

No API service layer exists. Need to create:
- API client with base configuration
- Request/response interceptors
- Error handling
- Type-safe API methods

## Integration Roadmap

### Phase 1: Foundation Setup

#### 1.1 Environment Configuration
Create `.env.local` file:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

Update `vite.config.ts` to expose environment variables:
```typescript
define: {
  'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
  'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
  'process.env.VITE_API_BASE_URL': JSON.stringify(env.VITE_API_BASE_URL || 'http://localhost:8000'),
}
```

#### 1.2 Update Type Definitions
Create `types/api.ts` with backend-aligned types:

```typescript
// Match backend API exactly
export interface RouteSubscription {
  id: string;  // UUID
  origin_country: string;  // 2-char code
  destination_country: string;
  visa_type: string;
  email: string;
  is_active: boolean;
  created_at: string;  // ISO 8601
  updated_at: string;
}

export interface SourceResponse {
  id: string;
  country: string;
  visa_type: string;
  url: string;
  name: string;
  fetch_type: 'html' | 'pdf';
  check_frequency: 'daily' | 'weekly' | 'custom';
  is_active: boolean;
  metadata: Record<string, any>;
  last_checked_at: string | null;
  last_change_detected_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PolicyChange {
  id: string;
  detected_at: string;
  source: {
    id: string;
    name: string;
    country: string;
    visa_type: string;
  };
  route: {
    id: string;
    origin_country: string;
    destination_country: string;
    visa_type: string;
    display: string;
  } | null;
  summary: string;
  is_new: boolean;
  diff_length: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  totalRoutes: number;
  totalSources: number;
  activeSources: number;
  changesLast7Days: number;
  changesLast30Days: number;
  recentChanges: PolicyChange[];
  sourceHealth: SourceHealth[];
}

export interface SourceHealth {
  sourceId: string;
  sourceName: string;
  country: string;
  visaType: string;
  lastCheckedAt: string | null;
  status: 'healthy' | 'stale' | 'error';
  consecutiveFailures: number;
  lastError: string | null;
}
```

#### 1.3 Create API Client
Create `services/api.ts`:

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          window.location.href = '/#/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { username, password });
    return response.data;
  }

  async logout() {
    await this.client.post('/auth/logout');
  }

  // Dashboard
  async getDashboard() {
    const response = await this.client.get('/api/dashboard');
    return response.data;
  }

  // Routes
  async getRoutes(params?: {
    page?: number;
    page_size?: number;
    origin_country?: string;
    destination_country?: string;
    visa_type?: string;
    is_active?: boolean;
  }) {
    const response = await this.client.get('/api/routes', { params });
    return response.data;
  }

  async createRoute(data: {
    origin_country: string;
    destination_country: string;
    visa_type: string;
    email: string;
    is_active?: boolean;
  }) {
    const response = await this.client.post('/api/routes', data);
    return response.data;
  }

  async getRoute(id: string) {
    const response = await this.client.get(`/api/routes/${id}`);
    return response.data;
  }

  async updateRoute(id: string, data: Partial<{
    origin_country: string;
    destination_country: string;
    visa_type: string;
    email: string;
    is_active: boolean;
  }>) {
    const response = await this.client.put(`/api/routes/${id}`, data);
    return response.data;
  }

  async deleteRoute(id: string) {
    await this.client.delete(`/api/routes/${id}`);
  }

  // Sources
  async getSources(params?: {
    page?: number;
    page_size?: number;
    country?: string;
    visa_type?: string;
    is_active?: boolean;
  }) {
    const response = await this.client.get('/api/sources', { params });
    return response.data;
  }

  async createSource(data: {
    country: string;
    visa_type: string;
    url: string;
    name: string;
    fetch_type: 'html' | 'pdf';
    check_frequency: 'daily' | 'weekly' | 'custom';
    is_active?: boolean;
    metadata?: Record<string, any>;
  }) {
    const response = await this.client.post('/api/sources', data);
    return response.data;
  }

  async getSource(id: string) {
    const response = await this.client.get(`/api/sources/${id}`);
    return response.data;
  }

  async updateSource(id: string, data: Partial<{
    country: string;
    visa_type: string;
    url: string;
    name: string;
    fetch_type: 'html' | 'pdf';
    check_frequency: 'daily' | 'weekly' | 'custom';
    is_active: boolean;
    metadata: Record<string, any>;
  }>) {
    const response = await this.client.put(`/api/sources/${id}`, data);
    return response.data;
  }

  async deleteSource(id: string) {
    await this.client.delete(`/api/sources/${id}`);
  }

  async triggerSource(id: string) {
    const response = await this.client.post(`/api/sources/${id}/trigger`);
    return response.data;
  }

  // Changes
  async getChanges(params?: {
    page?: number;
    page_size?: number;
    route_id?: string;
    source_id?: string;
    start_date?: string;
    end_date?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }) {
    const response = await this.client.get('/api/changes', { params });
    return response.data;
  }

  async getChange(id: string) {
    const response = await this.client.get(`/api/changes/${id}`);
    return response.data;
  }

  async downloadChangeDiff(id: string) {
    const response = await this.client.get(`/api/changes/${id}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async exportChanges(params?: {
    route_id?: string;
    source_id?: string;
    start_date?: string;
    end_date?: string;
  }) {
    const response = await this.client.get('/api/changes/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  // Jobs
  async triggerDailyFetch() {
    const response = await this.client.post('/api/jobs/daily-fetch');
    return response.data;
  }

  // Status
  async getStatus() {
    const response = await this.client.get('/api/status');
    return response.data;
  }
}

export const api = new ApiClient();
```

### Phase 2: Authentication Integration

#### 2.1 Update AuthContext
Replace mock authentication with real API calls:

```typescript
// context/AuthContext.tsx
import { api } from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('auth_token');
    if (token) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    try {
      setError(null);
      setIsLoading(true);
      const response = await api.login(username, password);
      localStorage.setItem('auth_token', response.access_token);
      setIsAuthenticated(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      // Continue with logout even if API call fails
    } finally {
      localStorage.removeItem('auth_token');
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, isLoading, error }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### 2.2 Update Login Page
Replace mock login with real API call:

```typescript
// pages/Login.tsx
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');
  setIsLoading(true);

  try {
    await login(email, password);
    navigate('/');
  } catch (err: any) {
    setError(err.response?.data?.detail || 'Invalid username or password');
  } finally {
    setIsLoading(false);
  }
};
```

### Phase 3: Data Integration

#### 3.1 Update Dashboard
Replace mock data with API calls:

```typescript
// pages/Dashboard.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardStats } from '../types/api';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const data = await api.getDashboard();
        setStats(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!stats) return null;

  // Use stats data instead of MOCK_STATS, MOCK_CHANGES, MOCK_SOURCES
  // ...
};
```

#### 3.2 Update RouteSubscriptions Page
Replace mock data with API calls:

```typescript
// pages/RouteSubscriptions.tsx
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { RouteSubscription, PaginatedResponse } from '../types/api';

const RouteSubscriptions: React.FC = () => {
  const [routes, setRoutes] = useState<RouteSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ page: 1, page_size: 20, total: 0 });

  useEffect(() => {
    fetchRoutes();
  }, [pagination.page]);

  const fetchRoutes = async () => {
    try {
      setLoading(true);
      const response: PaginatedResponse<RouteSubscription> = await api.getRoutes({
        page: pagination.page,
        page_size: pagination.page_size,
      });
      setRoutes(response.items);
      setPagination(prev => ({ ...prev, total: response.total }));
    } catch (err) {
      console.error('Failed to fetch routes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      await api.createRoute({
        origin_country: origin.toUpperCase().slice(0, 2), // Convert to 2-char code
        destination_country: destination.toUpperCase().slice(0, 2),
        visa_type: visaType,
        email: email, // Add email field to form
        is_active: true,
      });
      await fetchRoutes();
      setIsModalOpen(false);
      resetForm();
    } catch (err: any) {
      alert(err.response?.data?.detail?.message || 'Failed to create route');
    }
  };

  const handleDelete = async () => {
    if (deleteId) {
      try {
        await api.deleteRoute(deleteId);
        await fetchRoutes();
        setDeleteId(null);
      } catch (err) {
        alert('Failed to delete route');
      }
    }
  };

  // Update form to use country codes instead of full names
  // Add email field
  // ...
};
```

### Phase 4: Additional Dependencies

#### 4.1 Install Axios
```bash
npm install axios
```

#### 4.2 Update package.json
Add axios to dependencies:
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    // ... existing dependencies
  }
}
```

## Data Transformation Utilities

Create `utils/transform.ts` for converting between frontend display format and API format:

```typescript
// Country code mapping
export const COUNTRY_CODES: Record<string, string> = {
  'IN': 'India',
  'DE': 'Germany',
  'US': 'USA',
  'UK': 'United Kingdom',
  'CA': 'Canada',
  'FR': 'France',
  'AU': 'Australia',
  'JP': 'Japan',
};

export const COUNTRY_NAMES: Record<string, string> = Object.fromEntries(
  Object.entries(COUNTRY_CODES).map(([code, name]) => [name, code])
);

export function getCountryName(code: string): string {
  return COUNTRY_CODES[code.toUpperCase()] || code;
}

export function getCountryCode(name: string): string {
  return COUNTRY_NAMES[name] || name.toUpperCase().slice(0, 2);
}

// Status transformation
export function transformStatus(status: string): 'Healthy' | 'Stale' | 'Error' {
  const normalized = status.toLowerCase();
  if (normalized === 'healthy') return 'Healthy';
  if (normalized === 'stale') return 'Stale';
  if (normalized === 'error') return 'Error';
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
```

## Testing Checklist

### Authentication
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (error handling)
- [ ] Token storage and retrieval
- [ ] Token expiration handling
- [ ] Logout functionality
- [ ] Protected route access

### Dashboard
- [ ] Load dashboard stats
- [ ] Display recent changes
- [ ] Display source health
- [ ] Error handling for failed API calls
- [ ] Loading states

### Route Subscriptions
- [ ] List routes with pagination
- [ ] Create new route
- [ ] Update route
- [ ] Delete route
- [ ] Filter routes
- [ ] Form validation

### Sources
- [ ] List sources
- [ ] Create source
- [ ] Update source
- [ ] Delete source
- [ ] Trigger source fetch
- [ ] Display source status

### Changes
- [ ] List changes with filters
- [ ] View change detail
- [ ] Download diff
- [ ] Export to CSV
- [ ] Pagination

### Jobs
- [ ] Trigger daily fetch job
- [ ] Display job results
- [ ] Error handling

## CORS Configuration

Ensure backend CORS is configured to allow frontend origin:

```python
# api/config.py or api/main.py
CORS_ORIGINS = [
    "http://localhost:3000",  # Vite dev server
    "http://127.0.0.1:3000",
    # Add production URL when deployed
]
```

## Next Steps

1. **Immediate:**
   - Install axios: `npm install axios`
   - Create `.env.local` with API base URL
   - Create API service layer (`services/api.ts`)
   - Update type definitions to match backend

2. **Short-term:**
   - Integrate authentication
   - Replace mock data in Dashboard
   - Replace mock data in RouteSubscriptions
   - Add error handling and loading states

3. **Medium-term:**
   - Complete all page integrations
   - Add data transformation utilities
   - Implement proper error handling
   - Add loading indicators
   - Test all API endpoints

4. **Long-term:**
   - Add optimistic UI updates
   - Implement caching strategy
   - Add offline support
   - Performance optimization
   - Add unit tests for API service

## Notes

- The frontend uses **HashRouter** (`/#/routes`), which is fine for deployment but consider BrowserRouter for cleaner URLs
- The Swiss/Brutalist design is well-implemented and should be preserved
- All UI components are reusable and well-structured
- The mock data structure is close to the API but needs transformation layer
- Consider adding React Query or SWR for better data fetching and caching

