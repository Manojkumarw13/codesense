import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
}

export default function Card({ title, eyebrow, action, children }: CardProps) {
  return (
    <section className="card">
      {(title ?? eyebrow ?? action) && (
        <div className="card-head">
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            {title && <h2 className="card-title">{title}</h2>}
          </div>
          {action}
        </div>
      )}
      <div className="card-body">{children}</div>
    </section>
  );
}
