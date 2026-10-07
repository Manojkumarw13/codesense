import { useState } from 'react';
import { simulatorClient, type SimulatorStatus } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';
import EmptyArt from '../components/EmptyArt';
import Loading from '../components/ui/Loading';
import { useToast } from '../components/ui/Toast';

const SCENARIOS = [
  'NORMAL',
  'HIGH_LOAD',
  'REVIEW_BOTTLENECK',
  'CI_BOTTLENECK',
  'DEPLOYMENT_FAILURE',
  'INCIDENT_SPIKE',
  'RECOVERY',
];

export default function Simulator() {
  const status = useApi<SimulatorStatus>(() => simulatorClient.getStatus());
  const [scenario, setScenario] = useState('NORMAL');
  const [busy, setBusy] = useState(false);
  const toast = useToast();

  async function act(label: string, fn: () => Promise<{ message: string }>) {
    setBusy(true);
    try {
      const res = await fn();
      toast({ tone: 'ok', title: label, detail: res.message });
      status.reload();
    } catch (e) {
      toast({ tone: 'bad', title: label, detail: e instanceof Error ? e.message : 'Failed' });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2>Simulator</h2>
      <p className="muted">The external data source — live status and controls.</p>
      {status.loading ? (
        <Loading />
      ) : status.error || !status.data ? (
        <Card title="Simulator offline">
          <EmptyArt />
          <EmptyState message="Cannot reach the simulator. Start the :8001 service to generate demo data." />
        </Card>
      ) : (
        <>
          <div className="grid">
            <Card title="Status">
              <p>
                <Badge tone={status.data.is_running ? 'ok' : 'low'}>
                  {status.data.is_running
                    ? status.data.is_paused
                      ? 'PAUSED'
                      : 'RUNNING'
                    : 'STOPPED'}
                </Badge>{' '}
                <Badge tone="info">{status.data.current_scenario}</Badge>
              </p>
              <p className="muted">
                Simulated time: {new Date(status.data.simulated_time).toLocaleString()}
              </p>
            </Card>
            <Card title="Active entities">
              <ul className="list">
                {Object.entries(status.data.active_entities).map(([k, v]) => (
                  <li key={k}>
                    {k.replace(/_/g, ' ')}: <strong>{v}</strong>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
          <Card title="Controls">
            <div className="filters">
              <button className="btn" disabled={busy} onClick={() => act('Start', () => simulatorClient.start())}>
                Start
              </button>
              <button className="btn btn-secondary" disabled={busy} onClick={() => act('Stop', () => simulatorClient.stop())}>
                Stop
              </button>
              <label className="selector">
                Scenario
                <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
                  {SCENARIOS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="btn btn-secondary"
                disabled={busy}
                onClick={() => act('Scenario', () => simulatorClient.setScenario(scenario))}
              >
                Apply scenario
              </button>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
