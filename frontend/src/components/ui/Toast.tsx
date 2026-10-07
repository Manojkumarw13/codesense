import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react';

interface ToastItem {
  id: number;
  tone: 'ok' | 'bad' | 'info';
  title: string;
  detail?: string;
}

const ToastContext = createContext<(t: Omit<ToastItem, 'id'>) => void>(() => {});

/** Sonner-style bottom-right toasts: 180ms materialize, 4s Sonner-default dwell. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const [exiting, setExiting] = useState<Set<number>>(new Set());
  const nextId = useRef(1);

  const remove = useCallback((id: number) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
    setExiting((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const dismiss = useCallback(
    (id: number) => {
      setExiting((prev) => new Set(prev).add(id));
      window.setTimeout(() => remove(id), 160);
    },
    [remove],
  );

  const push = useCallback(
    (t: Omit<ToastItem, 'id'>) => {
      const id = nextId.current++;
      setItems((prev) => [...prev.slice(-3), { ...t, id }]);
      window.setTimeout(() => {
        dismiss(id);
      }, 4000);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toaster" aria-live="polite">
        {items.map((t) => (
          <div
            key={t.id}
            className={`toast toast-${t.tone}${exiting.has(t.id) ? ' toast-exiting' : ''}`}
            role="status"
          >
            <div>
              <div className="toast-title">{t.title}</div>
              {t.detail && <div className="toast-detail">{t.detail}</div>}
            </div>
            <button className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss">
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
