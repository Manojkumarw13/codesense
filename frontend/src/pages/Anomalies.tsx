import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import Loading from '../components/ui/Loading';
import FilterBar from '../components/FilterBar';
import SignalList from '../components/SignalList';

/** Anomalies: full signal list filtered by backend `severity` query param. */
export default function Anomalies() {
  const [severity, setSeverity] = useState('ALL');
  const [category, setCategory] = useState('ALL');

  const anomalies = useApi(
    () => apiClient.listAnomalies(severity === 'ALL' ? {} : { severity }),
    [severity],
  );

  if (anomalies.loading) {
    return (
      <div>
        <h1>Anomalies</h1>
        <Loading />
      </div>
    );
  }

  const all = anomalies.data ?? [];
  // Backend DOWN (or genuinely empty) → simulator EmptyState, never a dead page.
  if (anomalies.error || all.length === 0) {
    return (
      <div>
        <h1>Anomalies</h1>
        <EmptyState title="No anomalies yet" />
      </div>
    );
  }

  // Client-side guard in case the backend ignores the severity param.
  const items = all.filter(
    (item) =>
      (severity === 'ALL' || item.severity === severity) &&
      (category === 'ALL' ||
        String(
          (item as unknown as Record<string, unknown>).category ??
            (item as unknown as Record<string, unknown>).anomaly_type ??
            '',
        ).toLowerCase() === category.toLowerCase()),
  );

  return (
    <div>
      <h1>Anomalies</h1>
      <FilterBar
        severity={severity}
        onSeverityChange={setSeverity}
        category={category}
        onCategoryChange={setCategory}
      />
      <Card title="Anomalies">
        <SignalList
          items={items}
          basePath="/app/anomalies"
          emptyHint="No anomalies match these filters."
        />
      </Card>
    </div>
  );
}
