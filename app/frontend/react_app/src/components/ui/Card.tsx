import type { HTMLAttributes, ReactNode } from 'react';

export function Card({ className = '', children, ...props }: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <section className={`card-gradient rounded-3xl border border-clinical-border bg-white shadow-card ${className}`} {...props}>
      {children}
    </section>
  );
}

export function CardHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 border-b border-slate-100 p-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 className="font-display text-lg font-bold text-slate-950">{title}</h2>
        {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function CardBody({ className = '', children }: { className?: string; children: ReactNode }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}
