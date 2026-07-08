import type { ReactNode } from 'react';

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone = 'blue'
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
  tone?: 'blue' | 'green' | 'amber' | 'red' | 'slate' | 'model';
}) {
  const tones = {
    blue: 'bg-blue-50 text-blue-700 ring-blue-100',
    green: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    amber: 'bg-amber-50 text-amber-700 ring-amber-100',
    red: 'bg-red-50 text-red-700 ring-red-100',
    slate: 'bg-slate-100 text-slate-700 ring-slate-200',
    model: 'bg-teal-50 text-teal-700 ring-teal-100'
  };

  return (
    <div className="rounded-3xl border border-clinical-border bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-600">{label}</p>
          <p className="font-data mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
        </div>
        {icon ? <div className={`rounded-2xl p-3 ring-1 ${tones[tone]}`}>{icon}</div> : null}
      </div>
      {hint ? <p className="mt-4 text-xs font-medium text-slate-500">{hint}</p> : null}
    </div>
  );
}
