import { NavLink } from 'react-router-dom';

export const NAV_ITEMS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/health', label: 'Engineering Health' },
  { to: '/delivery', label: 'Delivery' },
  { to: '/development', label: 'Development Flow' },
  { to: '/cicd', label: 'CI/CD' },
  { to: '/reliability', label: 'Reliability' },
  { to: '/insights', label: 'Insights' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/bottlenecks', label: 'Bottlenecks' },
  { to: '/trends', label: 'Trends' },
  { to: '/integrations', label: 'Integrations' },
  { to: '/simulator', label: 'Simulator' },
  { to: '/ai-analysis', label: 'AI Analysis' },
  { to: '/settings', label: 'Settings' },
];

const NAV_GROUPS: { label: string; items: typeof NAV_ITEMS }[] = [
  { label: 'Analyze', items: NAV_ITEMS.slice(0, 2).concat(NAV_ITEMS.slice(9, 10)) },
  { label: 'Flows', items: NAV_ITEMS.slice(2, 6) },
  { label: 'Signals', items: NAV_ITEMS.slice(6, 9) },
  { label: 'System', items: NAV_ITEMS.slice(10) },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand">CodeSense</div>
      <nav>
        {NAV_GROUPS.map((g) => (
          <div key={g.label} className="nav-group">
            <div className="nav-group-label">{g.label}</div>
            {g.items.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                onClick={onClose}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                {n.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
