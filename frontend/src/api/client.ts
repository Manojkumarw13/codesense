// Single API seam — frontend never touches DB, only this typed client.
//
// NOTE: backend GET /metrics is Prometheus text, NOT JSON — there is no
// metric-definitions/values REST endpoint. Dashboards use the {items} list
// APIs below. Do not re-add /metrics JSON calls without a backend endpoint.
import type {
  AiStatus,
  Anomaly,
  Bottleneck,
  ExplainResponse,
  HealthResponse,
  HealthScore,
  Insight,
  ListEnvelope,
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

function qs(params: Record<string, string | number | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

/** Unwrap {total, items} envelopes; pass arrays straight through. */
export function unwrap<T>(payload: T[] | ListEnvelope<T>): T[] {
  if (Array.isArray(payload)) return payload;
  return payload.items ?? [];
}

export interface ListFilters {
  team_id?: string;
  severity?: string;
  category?: string;
  status?: string;
  limit?: number;
}

export const apiClient = {
  baseUrl: BASE_URL,
  getHealth: () => request<HealthResponse>('/health'),
  getHealthDetailed: () => request<unknown>('/health/detailed'),
  listEvents: (limit = 20) =>
    request<unknown>(`/events${qs({ limit })}`),

  listHealthScores: async (filters: ListFilters = {}) => {
    const payload = await request<HealthScore[] | ListEnvelope<HealthScore>>(
      `/health-score${qs(filters as Record<string, string | number | undefined>)}`,
    );
    return unwrap(payload);
  },
  getHealthScore: (id: string) => request<HealthScore>(`/health-score/${encodeURIComponent(id)}`),

  listInsights: async (filters: ListFilters = {}) => {
    const payload = await request<Insight[] | ListEnvelope<Insight>>(
      `/insights${qs(filters as Record<string, string | number | undefined>)}`,
    );
    return unwrap(payload);
  },
  getInsight: (id: string) => request<Insight>(`/insights/${encodeURIComponent(id)}`),

  listAnomalies: async (filters: ListFilters = {}) => {
    const payload = await request<Anomaly[] | ListEnvelope<Anomaly>>(
      `/anomalies${qs(filters as Record<string, string | number | undefined>)}`,
    );
    return unwrap(payload);
  },
  getAnomaly: (id: string) => request<Anomaly>(`/anomalies/${encodeURIComponent(id)}`),

  listBottlenecks: async (filters: ListFilters = {}) => {
    const payload = await request<Bottleneck[] | ListEnvelope<Bottleneck>>(
      `/bottlenecks${qs(filters as Record<string, string | number | undefined>)}`,
    );
    return unwrap(payload);
  },
  getBottleneck: (id: string) =>
    request<Bottleneck>(`/bottlenecks/${encodeURIComponent(id)}`),

  explain: (useCase: string) =>
    request<ExplainResponse>(`/ai/explain${qs({ use_case: useCase })}`, { method: 'POST' }),
  getAiStatus: () => request<AiStatus>('/ai/status'),
  listMlModels: async () => {
    const payload = await request<MlModel[] | ListEnvelope<MlModel>>('/ml/models');
    return unwrap(payload);
  },
  getMlFeatures: (teamId?: string) =>
    request<unknown>(`/ml/features${qs({ team_id: teamId })}`),
  getFusionStatus: () => request<unknown>('/ml/fusion/status'),
};
