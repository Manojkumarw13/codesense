import type { ReactNode } from 'react';

interface ToastProps {
  message: string;
  tone?: 'info' | 'success' | 'error';
  children?: ReactNode;
}

export default function Toast({ message, tone = 'info', children }: ToastProps) {
  return (
    <div role={tone === 'error' ? 'alert' : 'status'} data-tone={tone} className="toast">
      <span>{message}</span>
      {children}
    </div>
  );
}
