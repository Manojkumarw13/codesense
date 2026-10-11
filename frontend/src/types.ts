/** Shared DTO mirrors of the CodeSense backend (`/api/v1`). */

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type TimeRange = '24h' | '7d' | '30d' | '90d';

/** The six team-level health dimensions (PLAN.md §8). */
export const DIMENSIONS = [
  'Delivery Flow',
  'Development Flow',
  'Review Flow',
  'CI/CD Reliability',
  'Deployment Health',
  'Operational Health',
] as const;

export type Dimension = (typeof DIMENSIONS)[number];

export interface HealthScore {
  id: string;
  team_id: string;
  score: number;
  previous_score?: number | null;
  score_change?: number | null;
  dimensions?: Record<string, number> | null;
  computed_at?: string;
}

export interface Insight {
  id: string;
  type: string;
  category: string;
  severity: Severity;
  title: string;
  description: string;
  evidence?: unknown;
  confidence?: number | null;
  status?: string;
}

export interface Anomaly {
  id: string;
  severity: Severity;
  title?: string;
  description?: string;
  evidence?: unknown;
  confidence?: number | null;
}

export interface Bottleneck {
  id: string;
  category: 'REVIEW' | 'CI' | 'DEPLOYMENT' | 'WORKFLOW' | 'INCIDENT' | string;
  severity: Severity;
  title?: string;
  description?: string;
  evidence?: unknown;
}

export interface MlModel {
  id: string;
  name: string;
  scope: string;
  version?: string;
}

export interface ExplainResponse {
  explanation: string;
  source: 'RULE_ENGINE' | 'CLOUD_AI' | 'LOCAL_AI' | string;
}

export interface AiStatus {
  available: boolean;
  provider?: string;
}

export interface Paginated<T> {
  total: number;
  skip: number;
  limit: number;
  items: T[];
}
