import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { dimensionLabel } from '../types';
import Card from './ui/Card';
import Badge from './ui/Badge';
import ErrorState from './ui/ErrorState';
import EmptyState from './ui/EmptyState';
import Evidence from './Evidence';
import EmptyArt from './EmptyArt';
import { DashboardSkeleton } from './ui/Skeleton';
import { MiniSpark } from './charts/ScoreCharts';

export interface FlowConfig {
  title: string;
  blurb: string;
  dimensions: string[];
  bottleneckCategories: string[];
  keywords: string[];
}

/** Shared dashboard for Delivery / Development / CI-CD / Reliability. */
export default function FlowDashboard({ config }: { config: FlowConfig }) {
  const { teamId, timeRange } = useApp();
  const scores = useApi(() => apiClient.listHealthScores({ limit: 100 }));
  const bottlenecks = useApi(() => apiClient.listBottlenecks({ limit: 100 }));
  const anomalies = useApi(() => apiClient.listAnomalies({ limit: 20 }));
  const insights = useApi(() => apiClient.listInsights({ limit: 100 }));

  const loading = scores.loading || bottlenecks.loading || anomalies.loading || insights.loading;
  const error = scores.error ?? bottlenecks.error ?? anomalies.error ?? insights.error;

  if (loading) return <DashboardSkeleton />;
  if (error) return <ErrorState message={error} />;

  const history = scores.data ?? [];
  const latest = history[0];
  const kws = config.keywords.map((k) => k.toLowerCase());

  const relatedBottlenecks = (bottlenecks.data ?? []).filter((b) =>
    config.bottleneckCategories.includes(b.category),
  );
  const relatedInsights = (insights.data ?? []).filter((i) => {
    const hay = `${i.category ?? ''} ${i.title} ${i.content}`.toLowerCase();
    return kws.some((k) => hay.includes(k));
  });

  return (
    <div>
      <h2>{config.title}</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Range <strong>{timeRange}</strong> · {config.blurb}
      </p>
      {!latest ? (
        <Card title="No data yet">
          <EmptyArt />
          <EmptyState message="No health scores found. Run the simulator to generate engineering events." />
        </Card>
      ) : (
        <>
          <div className="grid">
            {config.dimensions.map((dim) => (
              <Card key={dim} title={dimensionLabel(dim)}>
                <div className="score-hero">
                  {typeof latest.component_metrics[dim] === 'number'
                    ? latest.component_metrics[dim].toFixed(1)
                    : '—'}
                </div>
                <MiniSpark
                  data={[...history]
                    .reverse()
                    .map((s) => s.component_metrics[dim])
                    .filter((v): v is number => typeof v === 'number')}
                />
              </Card>
            ))}
          </div>
          <div className="grid">
            <Card title={`Related bottlenecks (${relatedBottlenecks.length})`}>
              {relatedBottlenecks.length === 0 ? (
                <EmptyState message="No bottlenecks in this flow area." />
              ) : (
                <ul className="list">
                  {relatedBottlenecks.slice(0, 10).map((b) => (
                    <li key={b.id}>
                      <strong>{b.title}</strong>{' '}
                      <Badge tone={b.severity.toLowerCase()}>{b.severity}</Badge>
                      <Evidence data={b.evidence} />
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Recent anomalies">
              {(anomalies.data ?? []).length === 0 ? (
                <EmptyState message="No anomalies detected." />
              ) : (
                <ul className="list">
                  {(anomalies.data ?? []).slice(0, 10).map((a) => (
                    <li key={a.id}>
                      observed <strong>{a.observed_value}</strong> vs baseline{' '}
                      {a.baseline_value ?? '—'}{' '}
                      <Badge tone={a.severity.toLowerCase()}>{a.severity}</Badge>
                      <Evidence data={a.evidence} />
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
          <Card title={`Related insights (${relatedInsights.length})`}>
            {relatedInsights.length === 0 ? (
              <EmptyState message="No insights in this flow area yet." />
            ) : (
              <ul className="list">
                {relatedInsights.slice(0, 15).map((i) => (
                  <li key={i.id}>
                    <strong>{i.title}</strong>{' '}
                    {i.severity && <Badge tone={i.severity.toLowerCase()}>{i.severity}</Badge>}
                    <Evidence data={i.evidence} />
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
