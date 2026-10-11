import Card from '../components/ui/Card';

/** Settings: honest Phase 22 boundary placeholder with RBAC roles. */
export default function Settings() {
  return (
    <div>
      <h1>Settings</h1>
      <p className="page-sub">Workspace preferences land here in Phase 22.</p>
      <Card title="Access roles">
        <ul className="role-list">
          <li>
            <p className="role-name">Viewer</p>
            <p className="state-hint">Read-only access to dashboards and insights.</p>
          </li>
          <li>
            <p className="role-name">Maintainer</p>
            <p className="state-hint">Manage integrations and trigger simulator runs.</p>
          </li>
          <li>
            <p className="role-name">Admin</p>
            <p className="state-hint">Manage roles, billing, and workspace settings.</p>
          </li>
        </ul>
        <p className="state-hint">
          Role management is not editable yet. RBAC controls arrive with the Phase 22 boundary.
        </p>
      </Card>
    </div>
  );
}
