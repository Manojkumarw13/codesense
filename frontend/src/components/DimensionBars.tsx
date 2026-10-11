import { Bar, BarChart, ResponsiveContainer } from 'recharts';
import type { ComponentMetric } from '../types';

/** Snake_case `component_metrics` key → display label. Unknown keys render raw. */
export const DIMENSION_LABELS: Record<string, string> = {
  delivery_flow: 'Delivery Flow',
  development_flow: 'Development Flow',
  review_flow: 'Review Flow',
  'ci/cd_reliability': 'CI/CD Reliability',
  cicd_reliability: 'CI/CD Reliability',
  ci_cd_reliability: 'CI/CD Reliability',
  deployment_health: 'Deployment Health',
  operational_health: 'Operational Health',
};

export function dimensionLabel(key: string): string {
  return DIMENSION_LABELS[key] ?? DIMENSION_LABELS[key.toLowerCase()] ?? key;
}

export function dimensionValue(value: ComponentMetric | number): number {
  if (typeof value === 'number') return value;
  if (value && typeof value.score === 'number') return value.score;
  return 0;
}

interface DimensionBarsProps {
  metrics: Record<string, ComponentMetric | number>;
}

/** Horizontal bars from `HealthScore.component_metrics`. */
export default function DimensionBars({ metrics }: DimensionBarsProps) {
  const rows = Object.entries(metrics).map(([key, value]) => ({
    key,
    name: dimensionLabel(key),
    value: dimensionValue(value),
  }));
  return (
    <div className="dimension-bars">
      <ul className="dimension-list">
        {rows.map((row) => (
          <li key={row.key} className="dimension-row">
            <span className="dimension-name">{row.name}</span>
            <span className="dimension-value tnum">{row.value.toFixed(1)}</span>
          </li>
        ))}
      </ul>
      <div aria-hidden="true" style={{ height: Math.max(120, rows.length * 40) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={rows} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
            <Bar dataKey="value" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
