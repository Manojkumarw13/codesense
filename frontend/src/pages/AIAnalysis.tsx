import { useState } from 'react';
import { ApiError, apiClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import type { ExplainResponse } from '../types';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import ErrorState from '../components/ui/ErrorState';
import Input from '../components/ui/Input';
import Loading from '../components/ui/Loading';

const FALLBACK_INSIGHTS = [
  {
    title: 'Review latency rises on Fridays',
    detail: 'Deterministic rule: median time-to-first-review is highest at the end of the week.',
  },
  {
    title: 'CI failures cluster after large merges',
    detail: 'Deterministic rule: batches touching many services correlate with red pipelines.',
  },
  {
    title: 'Deploy frequency dips before releases',
    detail: 'Deterministic rule: change freeze windows reduce throughput ahead of milestones.',
  },
];

const FALLBACK_EXPLANATION =
  'AI explanation is unavailable for this input, so here is the deterministic summary instead.';

/** AIAnalysis: status-gated fallback notice + on-demand explain with 422 fallback. */
export default function AIAnalysis() {
  const [attempt, setAttempt] = useState(0);
  const aiStatus = useApi(() => apiClient.getAiStatus(), [attempt]);
  const [topic, setTopic] = useState('');
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [fallback, setFallback] = useState(false);
  const [explainError, setExplainError] = useState<string | null>(null);

  async function handleExplain() {
    setExplaining(true);
    setExplanation(null);
    setFallback(false);
    setExplainError(null);
    try {
      const result = await apiClient.postAiExplain({ topic: topic || 'team health' });
      setExplanation(result);
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        // Privacy-blocked input: render deterministic fallback content, never retry.
        setFallback(true);
      } else {
        setExplainError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setExplaining(false);
    }
  }

  if (aiStatus.loading) {
    return (
      <div>
        <h1>AI Analysis</h1>
        <Loading />
      </div>
    );
  }

  const status = aiStatus.data as unknown as { configured?: boolean; available?: boolean } | null;
  const configured = status?.configured ?? status?.available ?? false;

  return (
    <div>
      <h1>AI Analysis</h1>
      {!configured && (
        <Card title="AI is not configured">
          <p className="state-hint">
            AI explanations are turned off, so you are seeing deterministic insights instead. No
            data leaves this workspace.
          </p>
        </Card>
      )}
      {aiStatus.error && (
        <Card title="AI status">
          <p className="state-hint">
            Could not reach the AI status endpoint, so deterministic insights are shown instead.
          </p>
        </Card>
      )}
      <Card title="Deterministic insights">
        {FALLBACK_INSIGHTS.length === 0 ? (
          <EmptyState title="No insights yet" />
        ) : (
          <ul className="insight-list">
            {FALLBACK_INSIGHTS.map((insight) => (
              <li key={insight.title}>
                <p className="insight-title">{insight.title}</p>
                <p className="state-hint">{insight.detail}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title="On-demand explanation">
        <form
          className="explain-form"
          onSubmit={(event) => {
            event.preventDefault();
            void handleExplain();
          }}
        >
          <Input
            label="Topic"
            placeholder="e.g. delivery slowdown"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
          />
          <Button variant="primary" type="submit" disabled={explaining}>
            {explaining ? 'Explaining…' : 'Explain'}
          </Button>
        </form>
        {explaining && <Loading />}
        {explainError && (
          <ErrorState
            message={explainError}
            onRetry={() => {
              setAttempt((n) => n + 1);
              setExplainError(null);
            }}
          />
        )}
        {fallback && (
          <div className="fallback-block">
            <p className="state-title">Fallback summary</p>
            <p className="state-hint">{FALLBACK_EXPLANATION}</p>
          </div>
        )}
        {explanation && (
          <div className="explanation-block">
            <p className="state-title">Explanation ({explanation.source})</p>
            <p>{explanation.explanation}</p>
          </div>
        )}
      </Card>
    </div>
  );
}
