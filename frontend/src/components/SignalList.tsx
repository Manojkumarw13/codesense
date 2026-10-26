import { Link } from 'react-router-dom';
import Badge from './ui/Badge';

/** Minimal shape shared by insights, anomalies, and bottlenecks. */
export interface SignalListItem {
  id: string;
  title?: string | null;
  severity?: string | null;
}

interface SignalListProps {
  items: SignalListItem[];
  basePath: string;
  emptyTitle?: string;
  emptyHint?: string;
}

/**
 * Shared signal list (Task 5 → reused by Task 6).
 * Renders `Open →` links to `${basePath}/${id}`; empty renders the hint
 * (pages pass the "run the simulator" copy when the backend has no data).
 */
export default function SignalList({
  items,
  basePath,
  emptyTitle = 'No signals yet',
  emptyHint = 'Run the simulator to generate data.',
}: SignalListProps) {
  if (items.length === 0) {
    return (
      <div className="state-block">
        <p className="state-title">{emptyTitle}</p>
        <p className="state-hint">{emptyHint}</p>
      </div>
    );
  }

  return (
    <ul className="signal-list">
      {items.map((item) => (
        <li key={item.id} className="signal-row">
          <span className="signal-main">
            {item.severity && <Badge severity={item.severity}>{item.severity}</Badge>}
            <span className="signal-title">{item.title || 'Untitled signal'}</span>
          </span>
          <Link to={`${basePath}/${item.id}`}>Open →</Link>
        </li>
      ))}
    </ul>
  );
}
