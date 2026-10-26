import { Link, Outlet } from 'react-router-dom';

export default function PublicLayout() {
  return (
    <div className="public-shell">
      <header className="public-header">
        <Link to="/" className="public-brand">
          CodeSense
        </Link>
        <nav aria-label="Public">
          <Link to="/product">Product</Link>
          {' · '}
          <Link to="/docs">Docs</Link>
          {' · '}
          <Link to="/app">Open app</Link>
        </nav>
      </header>
      <Outlet />
      <footer className="public-footer">
        <p>
          CodeSense — team-level engineering health. <Link to="/product">Product</Link>
          {' · '}
          <Link to="/docs">Docs</Link>
          {' · '}
          <Link to="/app">Open dashboard</Link>
        </p>
      </footer>
    </div>
  );
}
