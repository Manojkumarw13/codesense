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

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand">CodeSense</div>
      <nav>
        {NAV_ITEMS.map((n) => (
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
      </nav>
    </aside>
  );
}
