// Single API seam — frontend never touches DB, only this typed client.
import type {
  Anomaly,
  Bottleneck,
  HealthResponse,
  HealthScore,
  Insight,
  MetricDefinition,
  MetricValue,
  MlModel,
} from '../types';

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  'http://localhost:8000/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `${init?.method ?? 'GET'} ${path} failed: ${res.status}`);
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v) q.set(k, v);
  const s = q.toString();
  return s ? `?${s}` : '';
}

export const apiClient = {
  baseUrl: BASE_URL,
  getHealth: () => request<HealthResponse>('/health'),
  getHealthDetailed: () => request<unknown>('/health/detailed'),
  listEvents: (limit = 20) => request<unknown>(`/events${qs({ limit: String(limit) })}`),
  getMetrics: () => request<MetricDefinition[] | { items: MetricDefinition[] }>('/metrics'),
  getMetricValues: (metricId: string, filters: Record<string, string | undefined> = {}) =>
    request<MetricValue[] | { items: MetricValue[] }>(
      `/metrics/${encodeURIComponent(metricId)}/values${qs(filters)}`,
    ),
  getHealthScore: (filters: Record<string, string | undefined> = {}) =>
    request<HealthScore[] | HealthScore>(`/health-score${qs(filters)}`),
  getInsights: () => request<Insight[] | { items: Insight[] }>('/insights'),
  getAnomalies: () => request<Anomaly[] | { items: Anomaly[] }>('/anomalies'),
  getBottlenecks: () => request<Bottleneck[] | { items: Bottleneck[] }>('/bottlenecks'),
  getRisk: (teamId: string) =>
    request<unknown>(`/teams/${encodeURIComponent(teamId)}/risk`),
  getMlModels: () => request<MlModel[] | { items: MlModel[] }>('/ml/models'),
  getMlFeatures: (teamId?: string) =>
    request<unknown>(`/ml/features${qs({ team_id: teamId })}`),
  getMlPredictions: () => request<unknown>('/ml/predictions'),
};
