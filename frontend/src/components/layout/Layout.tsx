import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

export default function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="shell">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="main-col">
        <Header onMenu={() => setOpen((v) => !v)} />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
