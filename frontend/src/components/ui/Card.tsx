import type { ReactNode } from 'react';

export default function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <section className="card">
      {title && <h3 className="card-title">{title}</h3>}
      <div>{children}</div>
    </section>
  );
}
