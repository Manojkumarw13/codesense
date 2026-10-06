import { dimensionLabel } from '../../types';

/** SVG bars for the 6 health-score dimensions (0–100 scale). */
export default function DimensionBars({ dims }: { dims: Record<string, number> }) {
  const entries = Object.entries(dims);
  if (entries.length === 0) return <p className="muted">No dimension data yet.</p>;
  return (
    <div className="dim-bars">
      {entries.map(([key, value]) => (
        <div key={key} className="dim-row">
          <span className="dim-label">{dimensionLabel(key)}</span>
          <div className="dim-track">
            <div
              className="dim-fill"
              style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
            />
          </div>
          <span className="dim-value">{value.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
}
