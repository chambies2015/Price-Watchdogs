const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';
const DEFAULT_TIMEOUT_MS = 10000;
const DEFAULT_RETRIES = 2;
const RETRY_BASE_DELAY_MS = 300;

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const method = options?.method?.toUpperCase() || 'GET';
  const isIdempotent = method === 'GET' || method === 'HEAD';
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const retries = isIdempotent ? DEFAULT_RETRIES : 0;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
    if (options?.signal) {
      if (options.signal.aborted) {
        controller.abort();
      } else {
        options.signal.addEventListener('abort', () => controller.abort(), { once: true });
      }
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        if (isIdempotent && response.status >= 500 && attempt < retries) {
          await sleep(RETRY_BASE_DELAY_MS * Math.pow(2, attempt));
          continue;
        }
        throw new ApiError(error.detail || `API error: ${response.statusText}`, response.status, error.detail);
      }

      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return undefined as T;
      }

      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      if (isIdempotent && attempt < retries) {
        await sleep(RETRY_BASE_DELAY_MS * Math.pow(2, attempt));
        continue;
      }
      if (error instanceof ApiError) {
        throw error;
      }
      const err = error as Error;
      if (err.name === 'AbortError') {
        throw new ApiError('Request timed out', 408);
      }
      throw err;
    }
  }

  throw new ApiError('Request failed', 500);
}

export interface User {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface DeleteAccountRequest {
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type CheckFrequency = 'daily' | 'weekly' | 'twice_daily';

export interface Service {
  id: string;
  user_id: string;
  name: string;
  url: string;
  check_frequency: CheckFrequency;
  last_checked_at: string | null;
  is_active: boolean;
  alerts_enabled: boolean;
  alert_confidence_threshold: number;
  slack_webhook_url: string | null;
  discord_webhook_url: string | null;
  alert_count_24h: number;
  created_at: string;
}

export interface ServiceCreate {
  name: string;
  url: string;
  check_frequency?: CheckFrequency;
}

export interface ServiceUpdate {
  name?: string;
  url?: string;
  check_frequency?: CheckFrequency;
  is_active?: boolean;
  alerts_enabled?: boolean;
  alert_confidence_threshold?: number;
  slack_webhook_url?: string | null;
  discord_webhook_url?: string | null;
}

export const authApi = {
  register: async (data: RegisterRequest): Promise<User> => {
    return apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    return apiRequest<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  getMe: async (): Promise<User> => {
    return apiRequest<User>('/auth/me');
  },

  forgotPassword: async (data: ForgotPasswordRequest): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  resetPassword: async (data: ResetPasswordRequest): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  changePassword: async (data: ChangePasswordRequest): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  deleteAccount: async (data: DeleteAccountRequest): Promise<{ success: boolean }> => {
    return apiRequest<{ success: boolean }>('/auth/delete-account', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

export const servicesApi = {
  create: async (data: ServiceCreate): Promise<Service> => {
    return apiRequest<Service>('/services', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  list: async (): Promise<Service[]> => {
    return apiRequest<Service[]>('/services');
  },
  
  get: async (id: string): Promise<Service> => {
    return apiRequest<Service>(`/services/${id}`);
  },
  
  update: async (id: string, data: ServiceUpdate): Promise<Service> => {
    return apiRequest<Service>(`/services/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
  
  delete: async (id: string): Promise<void> => {
    return apiRequest<void>(`/services/${id}`, {
      method: 'DELETE',
    });
  },
  
  triggerCheck: async (id: string): Promise<{ success: boolean; snapshot_id?: string; change_detected?: boolean; change_id?: string | null; error?: string }> => {
    return apiRequest(`/services/${id}/check`, {
      method: 'POST',
    });
  },
};

export type ChangeType = 'price_increase' | 'price_decrease' | 'new_plan_added' | 'plan_removed' | 'free_tier_removed' | 'unknown';

export interface ChangeEvent {
  id: string;
  service_id: string;
  old_snapshot_id: string | null;
  new_snapshot_id: string;
  change_type: ChangeType;
  summary: string;
  confidence_score: number;
  created_at: string;
}

export interface ChangeEventDetail extends ChangeEvent {
  old_snapshot: Snapshot | null;
  new_snapshot: Snapshot;
}

export interface Snapshot {
  id: string;
  service_id: string;
  raw_html_hash: string;
  normalized_content_hash: string;
  normalized_content: string;
  created_at: string;
}

export interface ChangeEventSummary {
  id: string;
  change_type: ChangeType;
  summary: string;
  confidence_score: number;
  created_at: string;
}

export interface ServiceSummary {
  id: string;
  name: string;
  url: string;
  is_active: boolean;
  check_frequency: CheckFrequency;
  last_checked_at: string | null;
  next_check_at: string | null;
  last_change_event: ChangeEventSummary | null;
  change_count: number;
  alerts_enabled: boolean;
}

export interface DashboardSummary {
  services: ServiceSummary[];
  total_services: number;
  active_services: number;
  recent_changes_count: number;
}

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    return apiRequest<DashboardSummary>('/dashboard/summary');
  },
};

export const changesApi = {
  getChangeEvent: async (id: string): Promise<ChangeEventDetail> => {
    return apiRequest<ChangeEventDetail>(`/services/changes/${id}`);
  },
  
  getServiceChanges: async (serviceId: string, limit: number = 20): Promise<ChangeEvent[]> => {
    return apiRequest<ChangeEvent[]>(`/services/${serviceId}/changes?limit=${limit}`);
  },
};

export const snapshotsApi = {
  getServiceSnapshots: async (serviceId: string, limit: number = 10): Promise<Snapshot[]> => {
    return apiRequest<Snapshot[]>(`/services/${serviceId}/snapshots?limit=${limit}`);
  },
  
  getSnapshot: async (serviceId: string, snapshotId: string): Promise<Snapshot> => {
    return apiRequest<Snapshot>(`/services/${serviceId}/snapshots/${snapshotId}`);
  },
};

export type PlanType = 'free' | 'pro_monthly' | 'pro_annual';
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'trialing';

export interface Subscription {
  id: string;
  user_id: string;
  plan_type: PlanType;
  status: SubscriptionStatus;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  service_limit: number | null;
  current_service_count: number;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: string;
  user_id: string;
  subscription_id: string | null;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface CheckoutSession {
  session_id: string;
  url: string;
}

export const subscriptionsApi = {
  getCurrent: async (): Promise<Subscription> => {
    return apiRequest<Subscription>('/subscriptions/current');
  },
  
  createCheckout: async (planType: PlanType): Promise<CheckoutSession> => {
    return apiRequest<CheckoutSession>('/subscriptions/create-checkout', {
      method: 'POST',
      body: JSON.stringify({ plan_type: planType }),
    });
  },
  
  cancel: async (): Promise<Subscription> => {
    return apiRequest<Subscription>('/subscriptions/cancel', {
      method: 'POST',
    });
  },
  
  getPayments: async (): Promise<Payment[]> => {
    return apiRequest<Payment[]>('/subscriptions/payments');
  },
};

