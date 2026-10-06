import type { ReactNode } from 'react';

export default function Badge({ tone = 'info', children }: { tone?: string; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
