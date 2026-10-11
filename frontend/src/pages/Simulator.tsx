import { useState } from 'react';
import { simulatorClient } from '../api/client';
import { useApi } from '../hooks/useApi';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import EmptyState from '../components/ui/EmptyState';
import Loading from '../components/ui/Loading';
import Select from '../components/ui/Select';
import Toast from '../components/ui/Toast';

const SCENARIOS = [
  { value: 'baseline', label: 'Baseline' },
  { value: 'high-load', label: 'High load' },
  { value: 'incident', label: 'Incident storm' },
];

function formatStatus(status: Record<string, unknown>): Array<[string, string]> {
  return Object.entries(status).map(([key, value]) => [
    key,
    typeof value === 'string' ? value : JSON.stringify(value),
  ]);
}

/** Simulator: operable demo loop (start/stop/scenario) with offline EmptyState. */
export default function Simulator() {
  const [attempt, setAttempt] = useState(0);
  const [scenario, setScenario] = useState(SCENARIOS[0].value);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const status = useApi(() => simulatorClient.getSimulatorStatus(), [attempt]);

  async function runAction(label: string, action: () => Promise<unknown>) {
    setBusy(true);
    setNotice(null);
    setActionError(null);
    try {
      await action();
      setNotice(label);
      setAttempt((n) => n + 1);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (status.loading) {
    return (
      <div>
        <h1>Simulator</h1>
        <Loading />
      </div>
    );
  }

  if (status.error || !status.data) {
    return (
      <div>
        <h1>Simulator</h1>
        <EmptyState
          title="Simulator unavailable"
          hint="The simulator backend (SIM_BASE) is unreachable. Start the simulator service and retry."
        />
        {notice && <Toast message={notice} tone="success" />}
        {actionError && <Toast message={actionError} tone="error" />}
      </div>
    );
  }

  const rows = formatStatus(status.data);
  return (
    <div>
      <h1>Simulator</h1>
      <p className="page-sub">Drive the demo loop: pick a scenario, start, then stop.</p>
      <Card
        title="Status"
        action={
          <div className="btn-row">
            <Button
              variant="primary"
              disabled={busy}
              onClick={() => void runAction('Simulator started', () => simulatorClient.startSimulator({ scenario }))}
            >
              Start
            </Button>
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => void runAction('Simulator stopped', () => simulatorClient.stopSimulator({}))}
            >
              Stop
            </Button>
          </div>
        }
      >
        {rows.length === 0 ? (
          <EmptyState title="No simulator status yet" hint="Start the simulator to generate data." />
        ) : (
          <dl className="kv-list">
            {rows.map(([key, value]) => (
              <div key={key} className="kv-row">
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </Card>
      <Card title="Scenario">
        <Select
          label="Scenario"
          options={SCENARIOS}
          value={scenario}
          disabled={busy}
          onChange={(event) => {
            const next = event.target.value;
            setScenario(next);
            void runAction(`Scenario set to ${next}`, () =>
              simulatorClient.setSimulatorScenario(next),
            );
          }}
        />
      </Card>
      {notice && <Toast message={notice} tone="success" />}
      {actionError && <Toast message={actionError} tone="error" />}
    </div>
  );
}
