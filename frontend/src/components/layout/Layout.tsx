import { useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

const SECTION_OF: [RegExp, string][] = [
  [/^\/(health|trends|$)/, 'Analyze'],
  [/^\/(delivery|development|cicd|reliability)/, 'Flows'],
  [/^\/(insights|anomalies|bottlenecks)/, 'Signals'],
  [/^\/(integrations|simulator|ai-analysis|settings)/, 'System'],
];

export function sectionFor(pathname: string): string {
  for (const [re, label] of SECTION_OF) if (re.test(pathname)) return label;
  return 'System';
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open ]);

  return (
    <div className="shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <Sidebar open={open} onClose={() => setOpen(false)} />
      {open && (
        <button className="scrim open" aria-label="Close navigation" onClick={() => setOpen(false)} />
      )}
      <div className="main-col">
        <Header onMenu={() => setOpen((v) => !v)} />
        <main className="content" id="main-content">
          <div key={pathname} className="page-enter">
            <div className="eyebrow">{sectionFor(pathname)}</div>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
