// Mirrors backend /api/v1 DTOs (team-level only — never individual identity).
// Field truth: backend/app/models/analytics.py + endpoints.

export interface HealthResponse {
  status: string;
  app?: string;
  env?: string;
}

export interface ListEnvelope<T> {
  total: number;
  skip: number;
  limit: number;
  items: T[];
}

export interface HealthScore {
  id: string;
  organization_id?: string | null;
  project_id?: string | null;
  team_id: string;
  period_start: string;
  period_end: string;
  score: number;
  previous_score?: number | null;
  score_change?: number | null;
  score_version?: string;
  component_metrics: Record<string, number>;
  calculated_at: string;
}

export interface Insight {
  id: string;
  organization_id?: string | null;
  team_id?: string | null;
  insight_type: string;
  category?: string | null;
  severity?: string | null;
  title: string;
  content: string;
  confidence?: number | null;
  evidence: Record<string, unknown>;
  source_metrics?: Record<string, unknown>;
  generated_by: string;
  status: string;
  created_at: string;
}

export interface Anomaly {
  id: string;
  organization_id?: string | null;
  team_id: string;
  metric_id: string;
  severity: string;
  baseline_value?: number | null;
  observed_value: number;
  change_percent?: number | null;
  confidence?: number | null;
  evidence: Record<string, unknown>;
  detected_at: string;
}

export interface Bottleneck {
  id: string;
  organization_id?: string | null;
  team_id: string;
  category: string;
  severity: string;
  title: string;
  description?: string | null;
  evidence: Record<string, unknown>;
  detected_at: string;
}

export interface MlModel {
  id?: string;
  model_name: string;
  model_version?: string;
  is_active?: boolean;
  created_at?: string;
}

export interface ExplainResponse {
  use_case: string;
  explanation: string;
  source: 'CLOUD_AI' | 'FALLBACK_RULES';
  model?: string | null;
  sanitized_context: Record<string, unknown>;
}

export interface AiStatus {
  configured: boolean;
  model?: string | null;
  mode: 'cloud_ai' | 'fallback_rules';
}

export const USE_CASES = [
  'score_explanation',
  'anomaly_explanation',
  'bottleneck_explanation',
  'trend_summary',
  'investigation_suggestions',
] as const;

export type TimeRange = '24h' | '7d' | '30d' | '90d';

// The six health-score dimensions (PLAN §8).
export const DIMENSIONS = [
  'delivery_flow',
  'development_flow',
  'review_flow',
  'cicd_reliability',
  'deployment_health',
  'operational_health',
] as const;

export type Dimension = (typeof DIMENSIONS)[number];

const DIMENSION_LABELS: Record<string, string> = {
  delivery_flow: 'Delivery Flow',
  development_flow: 'Development Flow',
  review_flow: 'Review Flow',
  cicd_reliability: 'CI/CD Reliability',
  deployment_health: 'Deployment Health',
  operational_health: 'Operational Health',
};

export function dimensionLabel(key: string): string {
  return DIMENSION_LABELS[key] ?? key;
}
