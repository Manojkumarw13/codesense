// Mirrors backend /api/v1 DTOs (team-level only — never individual identity).

export interface HealthResponse {
  status: string;
  app?: string;
  env?: string;
}

export interface MetricDefinition {
  id: string;
  name: string;
  category: string;
  description?: string;
}

export interface MetricValue {
  metric_id: string;
  team_id?: string | null;
  repository_id?: string | null;
  period: string;
  value: number;
  baseline?: number | null;
  change_pct?: number | null;
}

export interface HealthScore {
  id?: string;
  team_id?: string | null;
  score: number;
  previous_score?: number | null;
  score_change?: number | null;
  dimensions?: Record<string, number>;
  created_at?: string;
}

export interface Insight {
  id: string;
  title: string;
  description?: string;
  severity: string;
  category?: string;
  confidence?: number | null;
  evidence?: unknown;
}

export interface Anomaly {
  id: string;
  title?: string;
  severity: string;
  confidence?: number | null;
  evidence?: unknown;
}

export interface Bottleneck {
  id: string;
  category: string;
  severity: string;
  title?: string;
  evidence?: unknown;
}

export interface MlModel {
  name: string;
  version: string;
  scope?: string;
}

export type TimeRange = '24h' | '7d' | '30d' | '90d';
