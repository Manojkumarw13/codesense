import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import Loading from '../components/ui/Loading';
import Select from '../components/ui/Select';
import FilterBar from '../components/FilterBar';
import SignalList from '../components/SignalList';

function unique(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter((v): v is string => !!v))).sort();
}

function toOptions(values: string[], allLabel: string) {
  return [{ value: 'ALL', label: allLabel }, ...values.map((v) => ({ value: v, label: v }))];
}

/** Insights: full signal list with severity/category/status/source filters. */
export default function Insights() {
  const [severity, setSeverity] = useState('ALL');
  const [category, setCategory] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  const [generatedBy, setGeneratedBy] = useState('ALL');

  const insights = useApi(
    () =>
      apiClient.listInsights({
        ...(severity !== 'ALL' ? { severity } : {}),
        ...(category !== 'ALL' ? { category } : {}),
        ...(status !== 'ALL' ? { status } : {}),
        ...(generatedBy !== 'ALL' ? { generated_by: generatedBy } : {}),
      }),
    [severity, category, status, generatedBy],
  );

  if (insights.loading) {
    return (
      <div>
        <h1>Insights</h1>
        <Loading />
      </div>
    );
  }

  const all = insights.data ?? [];
  // Backend DOWN (or genuinely empty) → simulator EmptyState, never a dead page.
  if (insights.error || all.length === 0) {
    return (
      <div>
        <h1>Insights</h1>
        <EmptyState title="No insights yet" />
      </div>
    );
  }

  const categories = unique(all.map((item) => item.category));
  const statuses = unique(all.map((item) => item.status));
  const sources = unique(
    all.map((item) => (item as unknown as Record<string, unknown>).generated_by as string | null),
  );

  // Client-side guard in case the backend ignores a query param.
  const items = all.filter(
    (item) =>
      (severity === 'ALL' || item.severity === severity) &&
      (category === 'ALL' || (item.category ?? '').toLowerCase() === category.toLowerCase()) &&
      (status === 'ALL' || (item.status ?? '').toLowerCase() === status.toLowerCase()) &&
      (generatedBy === 'ALL' ||
        String((item as unknown as Record<string, unknown>).generated_by ?? '').toLowerCase() ===
          generatedBy.toLowerCase()),
  );

  return (
    <div>
      <h1>Insights</h1>
      <FilterBar
        severity={severity}
        onSeverityChange={setSeverity}
        category={category}
        onCategoryChange={setCategory}
        categories={categories}
      />
      <div className="filter-bar" role="group" aria-label="Insight source filters">
        <Select
          label="Status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          options={toOptions(statuses, 'All statuses')}
          style={{ minHeight: 44 }}
        />
        <Select
          label="Source"
          value={generatedBy}
          onChange={(event) => setGeneratedBy(event.target.value)}
          options={toOptions(sources, 'All sources')}
          style={{ minHeight: 44 }}
        />
      </div>
      <Card title="Insights">
        <SignalList
          items={items}
          basePath="/app/insights"
          emptyHint="No insights match these filters."
        />
      </Card>
    </div>
  );
}
