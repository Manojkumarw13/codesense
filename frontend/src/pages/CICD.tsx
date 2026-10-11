import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import type { ComponentMetric } from '../types';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import Loading from '../components/ui/Loading';
import FilterBar from '../components/FilterBar';
import SignalList from '../components/SignalList';
import { dimensionLabel, dimensionValue } from '../components/DimensionBars';

/** component_metrics keys for this flow (backend uses display labels; match either form). */
const DIMENSION_KEYS = ['cicd_reliability', 'ci/cd_reliability', 'ci_cd_reliability', 'CI/CD Reliability'];
const BOTTLENECK_CATEGORY = 'CI';
const INSIGHT_PATTERN = /ci|build|pipeline/i;

function findSlice(metrics: Record<string, ComponentMetric | number>) {
  for (const key of DIMENSION_KEYS) {
    const hit = Object.entries(metrics).find(([k]) => k.toLowerCase() === key.toLowerCase());
    if (hit) return { key: hit[0], value: dimensionValue(hit[1]) };
  }
  return null;
}

/** CI/CD: reliability slice + build/CI signals with Open links. */
export default function CICD() {
  const { teamId } = useApp();
  const [attempt, setAttempt] = useState(0);
  const [severity, setSeverity] = useState('ALL');
  const [category, setCategory] = useState('ALL');
  const retry = () => setAttempt((n) => n + 1);

  const scores = useApi(() => apiClient.listHealthScores(), [attempt]);
  const insights = useApi(
    () => apiClient.listInsights(severity === 'ALL' ? {} : { severity }),
    [attempt, severity],
  );
  const anomalies = useApi(
    () => apiClient.listAnomalies(severity === 'ALL' ? {} : { severity }),
    [attempt, severity],
  );
  const bottlenecks = useApi(
    () => apiClient.listBottlenecks(severity === 'ALL' ? {} : { severity }),
    [attempt, severity],
  );

  if (scores.loading || insights.loading || anomalies.loading || bottlenecks.loading) {
    return (
      <div>
        <h1>CI/CD</h1>
        <Loading />
      </div>
    );
  }

  const error = scores.error ?? insights.error ?? anomalies.error ?? bottlenecks.error;
  if (error) {
    return (
      <div>
        <h1>CI/CD</h1>
        <ErrorState message={error.message} onRetry={retry} />
      </div>
    );
  }

  const history = scores.data ?? [];
  if (history.length === 0) {
    return (
      <div>
        <h1>CI/CD</h1>
        <EmptyState title="No health scores yet" />
      </div>
    );
  }

  const latest = history[0];
  const slice = findSlice(latest.component_metrics ?? {});

  const allInsights = insights.data ?? [];
  const allAnomalies = anomalies.data ?? [];
  const allBottlenecks = bottlenecks.data ?? [];

  const matchesCategory = (value: string | undefined) =>
    category === 'ALL' || (value ?? '').toLowerCase() === category.toLowerCase();

  const domainInsights = allInsights.filter(
    (item) =>
      INSIGHT_PATTERN.test(`${item.category} ${item.type}`) && matchesCategory(item.category),
  );
  const domainBottlenecks = allBottlenecks.filter(
    (item) => item.category.toUpperCase() === BOTTLENECK_CATEGORY && matchesCategory(item.category),
  );

  const categories = Array.from(
    new Set([...allInsights.map((item) => item.category), ...allBottlenecks.map((item) => item.category)]),
  )
    .filter(Boolean)
    .sort();

  const hasSignals = allInsights.length + allAnomalies.length + allBottlenecks.length > 0;
  const filterActive = severity !== 'ALL' || category !== 'ALL';

  return (
    <div>
      <h1>CI/CD</h1>
      <p className="page-sub">Team {teamId}</p>
      <Card title={slice ? dimensionLabel(slice.key) : 'CI/CD reliability'}>
        {slice ? (
          <p className="dimension-value tnum">{slice.value.toFixed(1)}</p>
        ) : (
          <EmptyState title="No dimension data yet" />
        )}
      </Card>
      {!hasSignals && !filterActive ? (
        <EmptyState title="No signals yet" />
      ) : !hasSignals ? (
        <EmptyState title="No signals match these filters" hint="Try a different severity or category." />
      ) : (
        <>
          <FilterBar
            severity={severity}
            onSeverityChange={setSeverity}
            category={category}
            onCategoryChange={setCategory}
            categories={categories}
          />
          <Card title="Insights">
            <SignalList
              items={domainInsights}
              basePath="/app/insights"
              emptyHint="No build/CI insights match these filters."
            />
          </Card>
          <Card title="Anomalies">
            <SignalList
              items={allAnomalies}
              basePath="/app/anomalies"
              emptyHint="No anomalies match these filters."
            />
          </Card>
          <Card title="Bottlenecks">
            <SignalList
              items={domainBottlenecks}
              basePath="/app/bottlenecks"
              emptyHint="No CI bottlenecks match these filters."
            />
          </Card>
        </>
      )}
    </div>
  );
}
