import { Link, Outlet } from 'react-router-dom';

export default function PublicLayout() {
  return (
    <div className="public-shell">
      <header className="public-header">
        <Link to="/" className="public-brand">
          CodeSense
        </Link>
        <nav aria-label="Public">
          <Link to="/app">Open app</Link>
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
