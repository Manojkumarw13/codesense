import { useState } from 'react';
import { apiClient } from '../api/client';
import { useApp } from '../context/AppContext';
import { useApi } from '../hooks/useApi';
import { USE_CASES, type ExplainResponse } from '../types';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Loading from '../components/ui/Loading';
import ErrorState from '../components/ui/ErrorState';
import Evidence from '../components/Evidence';
import { useToast } from '../components/ui/Toast';

const USE_CASE_LABELS: Record<string, string> = {
  score_explanation: 'Score explanation',
  anomaly_explanation: 'Anomaly explanation',
  bottleneck_explanation: 'Bottleneck explanation',
  trend_summary: 'Trend summary',
  investigation_suggestions: 'Investigation suggestions',
};

export default function AIAnalysis() {
  const { teamId } = useApp();
  const status = useApi(() => apiClient.getAiStatus());
  const [useCase, setUseCase] = useState<string>(USE_CASES[0]);
  const [result, setResult] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.explain(useCase);
      setResult(res);
      toast({
        tone: res.source === 'CLOUD_AI' ? 'ok' : 'info',
        title: 'Explanation ready',
        detail: `Source: ${res.source}`,
      });
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Request failed';
      setError(message);
      toast({ tone: 'bad', title: 'Explanation failed', detail: message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>AI Analysis</h2>
      <p className="muted">
        Team <strong>{teamId}</strong> · Optional LLM explainer behind the privacy gateway.{' '}
        No developer identity is ever sent or displayed.
      </p>
      {status.loading ? (
        <Loading label="Checking AI status…" />
      ) : status.error ? (
        <ErrorState message={`AI status unreachable: ${status.error}`} />
      ) : (
        <p className="muted">
          Mode:{' '}
          <Badge tone={status.data?.mode === 'cloud_ai' ? 'ok' : 'info'}>
            {status.data?.mode === 'cloud_ai'
              ? `CLOUD AI (${status.data.model})`
              : 'FALLBACK RULES (no key configured)'}
          </Badge>
        </p>
      )}
      <Card title="Explain">
        <div className="filters">
          <label className="selector">
            Use case
            <select value={useCase} onChange={(e) => setUseCase(e.target.value)}>
              {USE_CASES.map((u) => (
                <option key={u} value={u}>
                  {USE_CASE_LABELS[u] ?? u}
                </option>
              ))}
            </select>
          </label>
          <button className="btn" onClick={run} disabled={loading} aria-busy={loading}>
            {loading && <span className="spinner" aria-hidden="true" />}
            {loading ? 'Explaining…' : 'Explain'}
          </button>
        </div>
      </Card>
      {error && <ErrorState message={error} />}
      {result && (
        <Card title={USE_CASE_LABELS[result.use_case] ?? result.use_case}>
          <p>
            <Badge tone={result.source === 'CLOUD_AI' ? 'ok' : 'info'}>{result.source}</Badge>{' '}
            {result.model && <span className="muted">{result.model}</span>}
          </p>
          <p>{result.explanation}</p>
          <Evidence data={result.sanitized_context} />
        </Card>
      )}
    </div>
  );
}
