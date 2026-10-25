import type {
  AiStatus,
  Anomaly,
  AuthUser,
  Bottleneck,
  ExplainResponse,
  HealthScore,
  Insight,
  LoginResponse,
  MlModel,
  RefreshResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';
const SIM_BASE = import.meta.env.VITE_SIM_BASE_URL ?? 'http://localhost:8001';

/** Bearer token stored in localStorage by AuthContext after login. */
const TOKEN_KEY = 'codesense_token';

function authHeaders(): HeadersInit {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export type QueryParams = Record<string, string | undefined>;

function buildQuery(params: QueryParams): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (!v) continue;
    if ((k === 'team_id' || k === 'organization_id' || k === 'project_id') && !UUID_RE.test(v))
      continue;
    qs.set(k, v);
  }
  return qs.size ? `?${qs}` : '';
}

async function unwrap<T>(res: Response, path: string): Promise<T> {
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${path}`);
  const body = await res.json();
  return (body && Array.isArray(body.items) ? body.items : body) as T;
}

async function get<T>(path: string, params: Record<string, string | undefined> = {}): Promise<T> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (!v) continue;
    if ((k === 'team_id' || k === 'organization_id' || k === 'project_id') && !UUID_RE.test(v)) continue;
    qs.set(k, v);
  }
  const res = await fetch(`${BASE_URL}${path}${qs.size ? `?${qs}` : ''}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${path}`);
  const body = await res.json();
  return (body && Array.isArray(body.items) ? body.items : body) as T;
}

async function post<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  });
  return unwrap<T>(res, path);
}

async function simGet<T>(path: string): Promise<T> {
  const res = await fetch(`${SIM_BASE}${path}`);
  return unwrap<T>(res, path);
}

async function simPost<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${SIM_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return unwrap<T>(res, path);
}

export const apiClient = {
  getHealth: (): Promise<Record<string, unknown>> => get('/health'),
  getDetailedHealth: (): Promise<Record<string, unknown>> => get('/health/detailed'),
  listHealthScores: (params: QueryParams = {}): Promise<HealthScore[]> =>
    get('/health-score', params),
  getHealthScore: (id: string): Promise<HealthScore> => get(`/health-score/${id}`),
  listInsights: (params: QueryParams = {}): Promise<Insight[]> => get('/insights', params),
  getInsight: (id: string): Promise<Insight> => get(`/insights/${id}`),
  listAnomalies: (params: QueryParams = {}): Promise<Anomaly[]> => get('/anomalies', params),
  getAnomaly: (id: string): Promise<Anomaly> => get(`/anomalies/${id}`),
  listBottlenecks: (params: QueryParams = {}): Promise<Bottleneck[]> =>
    get('/bottlenecks', params),
  getBottleneck: (id: string): Promise<Bottleneck> => get(`/bottlenecks/${id}`),
  getTeamRisk: (teamId: string): Promise<Record<string, unknown>> =>
    get(`/teams/${teamId}/risk`),
  listMlModels: (): Promise<MlModel[]> => get('/ml/models'),
  getMlFeatures: (params: QueryParams = {}): Promise<Record<string, unknown>[]> =>
    get('/ml/features', params),
  getMlPredictions: (params: QueryParams = {}): Promise<Record<string, unknown>[]> =>
    get('/ml/predictions', params),
  getAiStatus: (): Promise<AiStatus> => get('/ai/status'),
  postAiExplain: (payload: Record<string, unknown>): Promise<ExplainResponse> =>
    post('/ai/explain', payload),
  listEvents: (params: QueryParams = {}): Promise<Record<string, unknown>[]> =>
    get('/events', params),
  login: (email: string, password: string): Promise<LoginResponse> =>
    post('/auth/login', { email, password }),
  refresh: (refreshToken: string): Promise<RefreshResponse> =>
    post('/auth/refresh', { refresh_token: refreshToken }),
  me: (): Promise<AuthUser> => get('/auth/me'),
};

export const simulatorClient = {
  getSimulatorStatus: (): Promise<Record<string, unknown>> => simGet('/simulator/status'),
  startSimulator: (payload: Record<string, unknown> = {}): Promise<Record<string, unknown>> =>
    simPost('/simulator/start', payload),
  stopSimulator: (payload: Record<string, unknown> = {}): Promise<Record<string, unknown>> =>
    simPost('/simulator/stop', payload),
  setSimulatorScenario: (scenario: string): Promise<Record<string, unknown>> =>
    simPost('/simulator/scenario', { scenario }),
};

export { buildQuery };
