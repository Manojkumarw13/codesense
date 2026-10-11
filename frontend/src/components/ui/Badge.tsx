import type { ReactNode } from 'react';
import type { Severity } from '../../types';

interface BadgeProps {
  severity?: Severity | string;
  children: ReactNode;
}

export default function Badge({ severity = 'LOW', children }: BadgeProps) {
  return (
    <span data-severity={String(severity).toLowerCase()} className="badge">
      {children}
    </span>
  );
}
