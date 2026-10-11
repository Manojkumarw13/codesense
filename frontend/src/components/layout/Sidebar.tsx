import { NavLink } from 'react-router-dom';

interface NavItem {
  to: string;
  label: string;
  end?: boolean;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const GROUPS: NavGroup[] = [
  {
    title: 'Analyze',
    items: [
      { to: '/app', label: 'Overview', end: true },
      { to: '/app/health', label: 'Health' },
      { to: '/app/trends', label: 'Trends' },
      { to: '/app/ai-analysis', label: 'AI Analysis' },
    ],
  },
  {
    title: 'Flows',
    items: [
      { to: '/app/delivery', label: 'Delivery' },
      { to: '/app/development', label: 'Development' },
      { to: '/app/cicd', label: 'CI/CD' },
      { to: '/app/reliability', label: 'Reliability' },
    ],
  },
  {
    title: 'Signals',
    items: [
      { to: '/app/insights', label: 'Insights' },
      { to: '/app/anomalies', label: 'Anomalies' },
      { to: '/app/bottlenecks', label: 'Bottlenecks' },
    ],
  },
  {
    title: 'System',
    items: [
      { to: '/app/integrations', label: 'Integrations' },
      { to: '/app/simulator', label: 'Simulator' },
      { to: '/app/settings', label: 'Settings' },
    ],
  },
];

export default function Sidebar() {
  return (
    <nav aria-label="Primary" className="sidebar-nav">
      {GROUPS.map((group) => (
        <div key={group.title} className="sidebar-group">
          <p className="eyebrow sidebar-group-title">{group.title}</p>
          <ul className="sidebar-list">
            {group.items.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    isActive ? 'sidebar-link sidebar-link-active' : 'sidebar-link'
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );
}
