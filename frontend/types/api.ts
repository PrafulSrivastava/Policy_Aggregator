// API-aligned type definitions matching backend exactly

export interface RouteSubscription {
  id: string; // UUID
  origin_country: string; // 2-char code
  destination_country: string;
  visa_type: string;
  email: string;
  is_active: boolean;
  created_at: string; // ISO 8601
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

export interface PolicyChangeDetail extends PolicyChange {
  diff: string;
  source: {
    id: string;
    name: string;
    url: string;
    country: string;
    visa_type: string;
  };
  old_version: {
    id: string;
    content_hash: string;
    raw_text: string;
    fetched_at: string;
    content_length: number;
  };
  new_version: {
    id: string;
    content_hash: string;
    raw_text: string;
    fetched_at: string;
    content_length: number;
  };
  previous_change_id: string | null;
  next_change_id: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
}

export interface DashboardStats {
  totalRoutes: number;
  totalSources: number;
  activeSources: number;
  changesLast7Days: number;
  changesLast30Days: number;
  recentChanges: Array<{
    id: string;
    sourceId: string;
    sourceName: string;
    route: string;
    detectedAt: string;
    hasDiff: boolean;
    diffLength: number;
  }>;
  sourceHealth: Array<{
    sourceId: string;
    sourceName: string;
    country: string;
    visaType: string;
    lastCheckedAt: string | null;
    status: 'healthy' | 'stale' | 'error';
    consecutiveFailures: number;
    lastError: string | null;
  }>;
}

export interface SystemStatus {
  sources: Array<{
    id: string;
    name: string;
    country: string;
    visa_type: string;
    url: string;
    fetch_type: string;
    check_frequency: string;
    is_active: boolean;
    last_checked_at: string | null;
    last_change_detected_at: string | null;
    status: string;
    consecutive_fetch_failures: number;
    last_fetch_error: string | null;
    next_check_time: string | null;
  }>;
  statistics: {
    total_sources: number;
    healthy_sources: number;
    error_sources: number;
    stale_sources: number;
    never_checked_sources: number;
  };
  last_daily_job_run: string | null;
}

export interface TriggerSourceResponse {
  success: boolean;
  sourceId: string;
  changeDetected: boolean;
  policyVersionId: string | null;
  policyChangeId: string | null;
  error: string | null;
  fetchedAt: string | null;
}

export interface DailyFetchJobResponse {
  startedAt: string;
  completedAt: string | null;
  sourcesProcessed: number;
  sourcesSucceeded: number;
  sourcesFailed: number;
  changesDetected: number;
  alertsSent: number;
  errors: string[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface SignupRequest {
  email: string;
  password: string;
}

export interface UserInfo {
  id: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface SignupResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

