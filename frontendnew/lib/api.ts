/**
 * Gatimaan API Client
 * Connects Next.js frontend to FastAPI backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT_MS = 15000;

// ─── Auth helpers ───────────────────────────────────────────────────────────
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('gatimaan_token');
}

export function setToken(token: string): void {
  localStorage.setItem('gatimaan_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('gatimaan_token');
  localStorage.removeItem('gatimaan_user');
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: options?.signal || controller.signal,
      headers: { ...authHeaders(), ...(options?.headers || {}) },
    });
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      throw new Error(`Request timed out after ${API_TIMEOUT_MS / 1000}s: ${path}`);
    }
    throw new Error(`Unable to reach Gatimaan API: ${error?.message || 'network error'}`);
  } finally {
    clearTimeout(timeout);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API Error ${res.status}`);
  }
  return res.json();
}

export async function apiFetchWithFallback<T>(
  request: Promise<T>,
  fallback: T,
): Promise<{ data: T; error: Error | null }> {
  try {
    return { data: await request, error: null };
  } catch (error: any) {
    return { data: fallback, error: error instanceof Error ? error : new Error(String(error)) };
  }
}

// ─── Auth ────────────────────────────────────────────────────────────────────
export const auth = {
  login: (username: string, password: string) =>
    apiFetch<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  getDemoCredentials: () => apiFetch<any>('/auth/demo-credentials'),
};

// ─── Health ──────────────────────────────────────────────────────────────────
export const health = {
  check: () => apiFetch<{ status: string; prototype: boolean }>('/health'),
};

// ─── Tasks ───────────────────────────────────────────────────────────────────
export const tasks = {
  getAll: (params?: {
    department?: string;
    corridor_id?: string;
    priority_category?: string;
    status?: string;
    limit?: number;
  }) => {
    const q = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    );
    return apiFetch<{ tasks: MaintenanceTask[]; total: number }>(`/tasks?${q}`);
  },
  getById: (taskId: string) =>
    apiFetch<MaintenanceTask>(`/tasks/${taskId}`),
  calculatePriorities: () =>
    apiFetch<{ updated: number; failed?: number; errors?: string[]; distribution: PriorityDist }>('/tasks/calculate-priorities', {
      method: 'POST',
    }),
  getSummary: () =>
    apiFetch<TaskSummary>('/tasks/stats/summary'),
};

// ─── Trains ──────────────────────────────────────────────────────────────────
export const trains = {
  getAll: (params?: { corridor_id?: string; date?: string }) => {
    const q = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    );
    return apiFetch<{ trains: TrainSchedule[] }>(`/trains?${q}`);
  },
  getCorridors: () =>
    apiFetch<{ corridors: Corridor[] }>('/trains/corridors'),
  getBlockWindows: (params?: { corridor_id?: string; date?: string }) => {
    const q = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    );
    return apiFetch<{ windows: BlockWindow[] }>(`/trains/block-windows?${q}`);
  },
  getGoodsForecast: (corridorId?: string) =>
    apiFetch<{ forecasts: GoodsForecast[] }>(
      `/trains/goods-forecast${corridorId ? `?corridor_id=${corridorId}` : ''}`
    ),
};

// ─── Blocks ──────────────────────────────────────────────────────────────────
export const blocks = {
  generatePlan: (body: { planning_horizon: string; corridor_id?: string }) =>
    apiFetch<GeneratePlanResponse>('/blocks/generate-plan', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getPlans: () => apiFetch<{ runs: OptimizationRun[] }>('/blocks/plans'),
  getPlan: (id: string) =>
    apiFetch<{ run: OptimizationRun; blocks: OptimizedBlock[] }>(`/blocks/plans/${id}`),
  getOptimized: (params?: { date_from?: string; date_to?: string; corridor_id?: string }) => {
    const q = new URLSearchParams(
      Object.entries(params || {}).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)])
    );
    return apiFetch<{ blocks: OptimizedBlock[] }>(`/blocks/optimized?${q}`);
  },
  simulateScenario: (blockId: string) =>
    apiFetch<SimulateResponse>('/blocks/simulate-scenario', {
      method: 'POST',
      body: JSON.stringify({ block_id: blockId, scenario_type: 'train_conflict' }),
    }),
};

// ─── Analytics ───────────────────────────────────────────────────────────────
export const analytics = {
  get: () => apiFetch<AnalyticsResponse>('/analytics'),
  getCorridors: () => apiFetch<{ corridors: CorridorAnalytics[] }>('/analytics/corridors'),
};

// ─── Import ──────────────────────────────────────────────────────────────────
export const importData = {
  loadDemo: () =>
    apiFetch<{ message: string; results: ImportResult }>('/import/load-demo-data', {
      method: 'POST',
    }),
  clearData: () =>
    apiFetch<{ message: string }>('/import/clear-data', { method: 'POST' }),
  uploadTasksCsv: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    const token = getToken();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    return fetch(`${API_BASE}/import/csv/tasks`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
      signal: controller.signal,
    }).then(async (response) => {
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || `API Error ${response.status}`);
      return payload;
    }).catch((error: any) => {
      if (error?.name === 'AbortError') throw new Error(`Request timed out after ${API_TIMEOUT_MS / 1000}s: /import/csv/tasks`);
      throw error;
    }).finally(() => clearTimeout(timeout));
  },
};

// ─── Types ───────────────────────────────────────────────────────────────────
export interface User {
  username: string;
  name: string;
  role: string;
  department: string;
}

export interface MaintenanceTask {
  id: string;
  task_id: string;
  department: 'Engineering' | 'S&T' | 'Traction Distribution';
  asset_type: string;
  asset_name: string;
  corridor_id: string;
  location: string;
  latitude?: number;
  longitude?: number;
  task_type: string;
  description?: string;
  duration_hours: number;
  criticality: number;
  urgency: number;
  safety_risk: number;
  asset_importance: number;
  due_date?: string;
  overdue: boolean;
  status: string;
  compatible_departments?: string[];
  priority_score?: number;
  existing_priority_score?: number;
  ml_risk_probability?: number | null;
  ml_risk_category?: 'HIGH' | 'MEDIUM' | 'LOW' | null;
  ml_risk_explanation?: string | null;
  final_planning_score?: number;
  ml_model_available?: boolean;
  priority_category?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  score_breakdown?: PriorityScoreBreakdown;
  priority_explanation?: string;
  created_at?: string;
}

export interface PriorityScoreBreakdown {
  criticality_contribution: number;
  urgency_contribution: number;
  safety_risk_contribution: number;
  asset_importance_contribution: number;
  overdue_contribution: number;
  criticality_normalized?: number;
  urgency_normalized?: number;
  safety_risk_normalized?: number;
  asset_importance_normalized?: number;
  overdue_factor?: number;
}

export interface TrainSchedule {
  id: string;
  train_number: string;
  train_name: string;
  train_type: string;
  corridor_id: string;
  date: string;
  arrival_time?: string;
  departure_time: string;
  priority: number;
  is_goods_train: boolean;
}

export interface Corridor {
  id: string;
  corridor_id: string;
  corridor_name: string;
  from_station: string;
  to_station: string;
  distance_km?: number;
  zone?: string;
  division?: string;
  electrified: boolean;
}

export interface BlockWindow {
  id: string;
  corridor_id: string;
  date: string;
  start_time: string;
  end_time: string;
  available: boolean;
  reason?: string;
  maximum_duration?: number;
}

export interface GoodsForecast {
  id: string;
  corridor_id: string;
  date: string;
  expected_start_time: string;
  expected_end_time: string;
  probability: number;
  train_count: number;
}

export interface OptimizedBlock {
  id: string;
  block_id: string;
  corridor_id: string;
  date: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  optimization_score?: number;
  train_conflicts?: number;
  tasks_completed?: number;
  departments_involved?: string[];
  window_duration_hours?: number;
  utilization?: number;
  estimated_downtime?: number;
  explanation?: string;
  task_ids?: string[];
  created_at?: string;
  // From in-memory optimization
  tasks?: MaintenanceTask[];
  multi_department?: boolean;
  has_critical?: boolean;
  has_overdue?: boolean;
}

export interface OptimizationRun {
  id: string;
  planning_horizon: string;
  created_at: string;
  total_tasks: number;
  tasks_scheduled: number;
  total_block_hours: number;
  separate_blocks: number;
  train_conflicts: number;
  estimated_asset_availability?: number;
  baseline_block_hours?: number;
  optimized_block_hours?: number;
  improvement_percentage?: number;
}

export interface OptimizationResult {
  run_id: string;
  planning_horizon: string;
  blocks: OptimizedBlock[];
  baseline_blocks: OptimizedBlock[];
  metrics: OptimizationMetrics;
  improvement: ImprovementMetrics;
  unscheduled_tasks?: UnscheduledTask[];
  data_sources?: Record<string, { count?: number; kind?: string }>;
  data_note: string;
}

export interface UnscheduledTask {
  task_id: string;
  department?: string;
  corridor_id?: string;
  priority_category?: string;
  priority_score?: number;
  reason: string;
}

export type GeneratePlanResponse = OptimizationResult;

export interface OptimizationMetrics {
  total_tasks?: number;
  tasks_scheduled?: number;
  total_block_hours?: number;
  separate_blocks?: number;
  train_conflicts?: number;
  multi_department_blocks?: number;
  average_utilization?: number;
  solver_status?: string;
}

export interface ImprovementMetrics {
  baseline_block_hours: number;
  optimized_block_hours: number;
  hours_saved: number;
  improvement_percentage: number;
  baseline_blocks: number;
  optimized_blocks_count: number;
  blocks_reduced: number;
  baseline_conflicts: number;
  optimized_conflicts: number;
  conflict_reduction: number;
  availability_before?: number | null;
  availability_after?: number | null;
  availability_improvement?: number | null;
  asset_impact?: {
    metric: string;
    baseline: number;
    optimized: number;
    total_pending: number;
    optimized_risk_coverage_percent?: number | null;
  };
  asset_availability?: {
    status: string;
    value?: number | null;
    reason?: string;
  };
  tasks_scheduled: number;
  total_tasks: number;
  multi_department_blocks: number;
  note: string;
}

export interface SimulateResponse {
  original_block: OptimizedBlock;
  conflict_detected: boolean;
  rescheduled_block: OptimizedBlock;
  message: string;
}

export interface AnalyticsResponse {
  summary: {
    total_tasks: number;
    completed: number;
    overdue: number;
    pending: number;
    scheduled: number;
    total_blocks: number;
    total_block_hours: number;
    multi_dept_blocks: number;
    total_conflicts: number;
    asset_availability?: number | null;
    asset_availability_note?: string;
  };
  priority_distribution: PriorityDist;
  department_distribution: Record<string, number>;
  comparison?: {
    baseline_block_hours?: number | null;
    optimized_block_hours?: number | null;
    improvement_percentage?: number | null;
    baseline_blocks?: number | null;
    optimized_blocks?: number | null;
    baseline_tasks_scheduled?: number | null;
    optimized_tasks_scheduled?: number | null;
    baseline_conflicts?: number | null;
    optimized_conflicts?: number | null;
    note: string;
  };
  weekly_trend: WeeklyTrend[];
  recent_runs: OptimizationRun[];
}

export interface PriorityDist {
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

export interface WeeklyTrend {
  date: string;
  day: string;
  blocks: number;
  hours: number;
  tasks: number;
  utilization?: number | null;
}

export interface TaskSummary {
  total: number;
  overdue: number;
  by_status: Record<string, number>;
  by_department: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface ImportResult {
  corridors: number;
  tasks: number;
  trains: number;
  forecasts: number;
  windows: number;
  errors: string[];
  received?: number;
  imported?: number;
  rejected?: number;
  warnings?: string[];
  warnings_count?: number;
}

export interface CorridorAnalytics {
  corridor_id: string;
  corridor_name: string;
  task_count: number;
  overdue_tasks: number;
  critical_tasks: number;
  block_count: number;
  block_hours: number;
}
