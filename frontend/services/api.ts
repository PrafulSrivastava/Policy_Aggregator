import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  RouteSubscription,
  SourceResponse,
  PolicyChange,
  PolicyChangeDetail,
  PaginatedResponse,
  DashboardStats,
  SystemStatus,
  TriggerSourceResponse,
  DailyFetchJobResponse,
  LoginRequest,
  LoginResponse,
  SignupRequest,
  SignupResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    console.log('[API] Initializing API client...');
    console.log('[API] Base URL:', API_BASE_URL);
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Include cookies in requests (for OAuth cookie-based auth)
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
          console.log('[API] Request:', config.method?.toUpperCase(), config.url, '- Token attached');
        } else {
          console.log('[API] Request:', config.method?.toUpperCase(), config.url, '- No token');
        }
        return config;
      },
      (error) => {
        console.error('[API] ❌ Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => {
        console.log('[API] ✅ Response:', response.config.method?.toUpperCase(), response.config.url, '- Status:', response.status);
        return response;
      },
      async (error: AxiosError) => {
        console.error('[API] ❌ Response error:', error.config?.method?.toUpperCase(), error.config?.url);
        console.error('[API] Error status:', error.response?.status);
        console.error('[API] Error data:', error.response?.data);
        if (error.response?.status === 401) {
          console.log('[API] 401 Unauthorized - removing token and redirecting');
          // Token expired or invalid
          localStorage.removeItem('auth_token');
          // Only redirect if not already on login page
          if (window.location.hash !== '#/login') {
            console.log('[API] Redirecting to login...');
            window.location.href = '/#/login';
          }
        }
        return Promise.reject(error);
      }
    );
    console.log('[API] ✅ API client initialized');
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    return response.data;
  }

  async signup(credentials: SignupRequest): Promise<SignupResponse> {
    const response = await this.client.post<SignupResponse>('/auth/signup', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  // OAuth endpoints
  initiateGoogleOAuth(): void {
    // Redirect to backend OAuth endpoint
    // The backend will handle the OAuth flow and redirect to Google
    window.location.href = `${API_BASE_URL}/auth/google`;
  }

  async checkOAuthAvailability(): Promise<boolean> {
    try {
      console.log('[API] Checking OAuth availability...');
      // Use fetch instead of axios for better redirect handling
      // Make a GET request with redirect: 'manual' to detect redirect without following it
      const response = await fetch(`${API_BASE_URL}/auth/google`, {
        method: 'GET',
        credentials: 'include', // Include cookies
        redirect: 'manual' // Don't follow redirects automatically
      });
      
      console.log('[API] OAuth check response status:', response.status);
      
      // 302 means redirect (OAuth is configured and will redirect to Google)
      // 501 means not implemented (OAuth is not configured)
      const isAvailable = response.status === 302;
      console.log('[API] OAuth available:', isAvailable);
      return isAvailable;
    } catch (error: any) {
      console.log('[API] OAuth availability check error:', error);
      // For network errors or other issues, assume OAuth is not available
      console.warn('[API] OAuth availability check failed:', error.message || error);
      return false;
    }
  }

  async verifyAuth(): Promise<boolean> {
    try {
      // Try to access a protected endpoint to verify authentication
      // The cookie will be sent automatically if present
      await this.client.get('/api/dashboard');
      return true;
    } catch (error: any) {
      if (error.response?.status === 401) {
        return false;
      }
      throw error;
    }
  }

  // Dashboard
  async getDashboard(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/api/dashboard');
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
  }): Promise<PaginatedResponse<RouteSubscription>> {
    const response = await this.client.get<PaginatedResponse<RouteSubscription>>('/api/routes', { params });
    return response.data;
  }

  async createRoute(data: {
    origin_country: string;
    destination_country: string;
    visa_type: string;
    email: string;
    is_active?: boolean;
  }): Promise<RouteSubscription> {
    const response = await this.client.post<RouteSubscription>('/api/routes', data);
    return response.data;
  }

  async getRoute(id: string): Promise<RouteSubscription> {
    const response = await this.client.get<RouteSubscription>(`/api/routes/${id}`);
    return response.data;
  }

  async updateRoute(
    id: string,
    data: Partial<{
      origin_country: string;
      destination_country: string;
      visa_type: string;
      email: string;
      is_active: boolean;
    }>
  ): Promise<RouteSubscription> {
    const response = await this.client.put<RouteSubscription>(`/api/routes/${id}`, data);
    return response.data;
  }

  async deleteRoute(id: string): Promise<void> {
    await this.client.delete(`/api/routes/${id}`);
  }

  // Sources
  async getSources(params?: {
    page?: number;
    page_size?: number;
    country?: string;
    visa_type?: string;
    is_active?: boolean;
  }): Promise<PaginatedResponse<SourceResponse>> {
    const response = await this.client.get<PaginatedResponse<SourceResponse>>('/api/sources', { params });
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
  }): Promise<SourceResponse> {
    const response = await this.client.post<SourceResponse>('/api/sources', data);
    return response.data;
  }

  async getSource(id: string): Promise<SourceResponse> {
    const response = await this.client.get<SourceResponse>(`/api/sources/${id}`);
    return response.data;
  }

  async updateSource(
    id: string,
    data: Partial<{
      country: string;
      visa_type: string;
      url: string;
      name: string;
      fetch_type: 'html' | 'pdf';
      check_frequency: 'daily' | 'weekly' | 'custom';
      is_active: boolean;
      metadata: Record<string, any>;
    }>
  ): Promise<SourceResponse> {
    const response = await this.client.put<SourceResponse>(`/api/sources/${id}`, data);
    return response.data;
  }

  async deleteSource(id: string): Promise<void> {
    await this.client.delete(`/api/sources/${id}`);
  }

  async triggerSource(id: string): Promise<TriggerSourceResponse> {
    const response = await this.client.post<TriggerSourceResponse>(`/api/sources/${id}/trigger`);
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
  }): Promise<PaginatedResponse<PolicyChange>> {
    const response = await this.client.get<PaginatedResponse<PolicyChange>>('/api/changes', { params });
    return response.data;
  }

  async getChange(id: string): Promise<PolicyChangeDetail> {
    const response = await this.client.get<PolicyChangeDetail>(`/api/changes/${id}`);
    return response.data;
  }

  async downloadChangeDiff(id: string): Promise<Blob> {
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
  }): Promise<Blob> {
    const response = await this.client.get('/api/changes/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  // Jobs
  async triggerDailyFetch(): Promise<DailyFetchJobResponse> {
    const response = await this.client.post<DailyFetchJobResponse>('/api/jobs/daily-fetch');
    return response.data;
  }

  // Status
  async getStatus(): Promise<SystemStatus> {
    const response = await this.client.get<SystemStatus>('/api/status');
    return response.data;
  }
}

export const api = new ApiClient();

