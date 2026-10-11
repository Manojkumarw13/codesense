import { useCallback, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

function eyebrowForPath(pathname: string): string {
  if (
    pathname === '/app' ||
    pathname.startsWith('/app/health') ||
    pathname.startsWith('/app/trends') ||
    pathname.startsWith('/app/ai-analysis')
  )
    return 'Analyze';
  if (
    pathname.startsWith('/app/delivery') ||
    pathname.startsWith('/app/development') ||
    pathname.startsWith('/app/cicd') ||
    pathname.startsWith('/app/reliability')
  )
    return 'Flows';
  if (
    pathname.startsWith('/app/insights') ||
    pathname.startsWith('/app/anomalies') ||
    pathname.startsWith('/app/bottlenecks')
  )
    return 'Signals';
  return 'System';
}

export default function Layout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();
  const eyebrow = eyebrowForPath(location.pathname);

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') closeDrawer();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [closeDrawer]);

  useEffect(() => {
    closeDrawer();
  }, [location.pathname, closeDrawer]);

  return (
    <div className="app-shell">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <aside className={`app-sidebar${drawerOpen ? ' app-sidebar-open' : ''}`} aria-label="App navigation">
        <span className="sidebar-brand">CodeSense</span>
        <Sidebar />
      </aside>
      {drawerOpen && (
        <button
          type="button"
          className="scrim"
          aria-label="Close navigation"
          onClick={closeDrawer}
        />
      )}
      <div className="app-main">
        <Header onMenuClick={() => setDrawerOpen((open) => !open)} />
        <div className="app-content">
          <p className="eyebrow">{eyebrow}</p>
          <main id="main-content" tabIndex={-1}>
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
