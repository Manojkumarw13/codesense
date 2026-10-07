import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { DIMENSIONS } from '../types';
import Card from '../components/ui/Card';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import EmptyArt from '../components/EmptyArt';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { MultiTrend, ScoreArea } from '../components/charts/ScoreCharts';

export default function Trends() {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 100 }));

  if (scores.loading) return <DashboardSkeleton />;
  if (scores.error) return <ErrorState message={scores.error} />;

  const items = scores.data ?? [];
  const chrono = [...items].reverse();
  const labelOf = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

  return (
    <div>
      <h1>Trends</h1>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong> · Historical
        baselines and score trajectory
      </p>
      {items.length === 0 ? (
        <Card title="No trend data">
          <EmptyArt />
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <Card title="Engineering Health Score over time">
            <ScoreArea
              data={chrono.map((s) => ({ label: labelOf(s.period_end), score: s.score }))}
              height={240}
            />
          </Card>
          <Card title="Dimensions over time">
            <MultiTrend
              data={chrono.map((s) => ({
                label: labelOf(s.period_end),
                ...Object.fromEntries(
                  DIMENSIONS.map((d) => [
                    d,
                    typeof s.component_metrics[d] === 'number'
                      ? (s.component_metrics[d] as number)
                      : 0,
                  ]),
                ),
              }))}
              series={[...DIMENSIONS]}
            />
          </Card>
        </>
      )}
    </div>
  );
}
