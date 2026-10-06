import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { DIMENSIONS, dimensionLabel } from '../types';
import Card from '../components/ui/Card';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import ScoreTrend from '../components/charts/ScoreTrend';

export default function Trends() {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 100 }));

  if (scores.loading) return <Loading />;
  if (scores.error) return <ErrorState message={scores.error} />;

  const items = scores.data ?? [];
  const chrono = [...items].reverse();

  return (
    <div>
      <h2>Trends</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong> · Historical
        baselines and score trajectory
      </p>
      {items.length === 0 ? (
        <Card title="No trend data">
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <Card title="Engineering Health Score over time">
            <ScoreTrend scores={chrono.map((s) => s.score)} width={720} height={180} />
          </Card>
          <div className="grid">
            {DIMENSIONS.map((dim) => (
              <Card key={dim} title={dimensionLabel(dim)}>
                <ScoreTrend
                  scores={chrono
                    .map((s) => s.component_metrics[dim])
                    .filter((v): v is number => typeof v === 'number')}
                  width={320}
                  height={100}
                />
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
