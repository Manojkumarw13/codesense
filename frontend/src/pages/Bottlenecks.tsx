import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import Loading from '../components/ui/Loading';
import FilterBar from '../components/FilterBar';
import SignalList from '../components/SignalList';

/** Bottlenecks: full signal list with backend `severity`/`category` filters. */
export default function Bottlenecks() {
  const [severity, setSeverity] = useState('ALL');
  const [category, setCategory] = useState('ALL');

  const bottlenecks = useApi(
    () =>
      apiClient.listBottlenecks({
        ...(severity !== 'ALL' ? { severity } : {}),
        ...(category !== 'ALL' ? { category } : {}),
      }),
    [severity, category],
  );

  if (bottlenecks.loading) {
    return (
      <div>
        <h1>Bottlenecks</h1>
        <Loading />
      </div>
    );
  }

  const all = bottlenecks.data ?? [];
  // Backend DOWN (or genuinely empty) → simulator EmptyState, never a dead page.
  if (bottlenecks.error || all.length === 0) {
    return (
      <div>
        <h1>Bottlenecks</h1>
        <EmptyState title="No bottlenecks yet" />
      </div>
    );
  }

  const categories = Array.from(new Set(all.map((item) => item.category)))
    .filter(Boolean)
    .sort();

  // Client-side guard in case the backend ignores a query param.
  const items = all.filter(
    (item) =>
      (severity === 'ALL' || item.severity === severity) &&
      (category === 'ALL' || item.category.toLowerCase() === category.toLowerCase()),
  );

  return (
    <div>
      <h1>Bottlenecks</h1>
      <FilterBar
        severity={severity}
        onSeverityChange={setSeverity}
        category={category}
        onCategoryChange={setCategory}
        categories={categories}
      />
      <Card title="Bottlenecks">
        <SignalList
          items={items}
          basePath="/app/bottlenecks"
          emptyHint="No bottlenecks match these filters."
        />
      </Card>
    </div>
  );
}
