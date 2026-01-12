const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `API error: ${response.statusText}`);
  }

  return response.json();
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
  last_checked_at: string | null;
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

