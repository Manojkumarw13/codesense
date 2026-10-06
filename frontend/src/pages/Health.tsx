import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import EmptyArt from '../components/EmptyArt';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { DimensionBarsChart, ScoreArea } from '../components/charts/ScoreCharts';

export default function Health() {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 100 }));

  if (scores.loading) return <DashboardSkeleton />;
  if (scores.error) return <ErrorState message={scores.error} />;

  const items = scores.data ?? [];
  const latest = items[0];
  const chrono = [...items].reverse();
  const labelOf = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

  return (
    <div>
      <h2>Engineering Health</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong> · Score →
        Dimension → Metric → Evidence
      </p>
      {items.length === 0 ? (
        <Card title="No scores yet">
          <EmptyArt />
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <div className="grid">
            <Card title="Current score">
              <div className="score-hero">{latest.score.toFixed(1)}</div>
              {latest.previous_score != null && (
                <p className="muted">Previous: {latest.previous_score.toFixed(1)}</p>
              )}
              {latest.score_change != null && (
                <Badge tone={latest.score_change >= 0 ? 'ok' : 'bad'}>
                  {latest.score_change >= 0 ? '+' : ''}
                  {latest.score_change.toFixed(1)}
                </Badge>
              )}
            </Card>
            <Card title="Dimensions (0–100)">
              <DimensionBarsChart dims={latest.component_metrics} />
            </Card>
          </div>
          <Card title="Score history">
            <ScoreArea
              data={chrono.map((s) => ({ label: labelOf(s.period_end), score: s.score }))}
            />
            <table className="table">
              <thead>
                <tr>
                  <th>Period end</th>
                  <th>Score</th>
                  <th>Change</th>
                  <th>Calculated</th>
                </tr>
              </thead>
              <tbody>
                {items.slice(0, 20).map((s) => (
                  <tr key={s.id}>
                    <td>{new Date(s.period_end).toLocaleString()}</td>
                    <td>{s.score.toFixed(1)}</td>
                    <td>{s.score_change != null ? s.score_change.toFixed(1) : '—'}</td>
                    <td>{new Date(s.calculated_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}
