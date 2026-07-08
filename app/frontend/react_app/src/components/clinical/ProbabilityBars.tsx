import { formatPercent } from '@/lib/formatters';

export function ProbabilityBars({ probabilities, highlight }: { probabilities: Record<string, number>; highlight?: string }) {
  const rows = Object.entries(probabilities).sort(([a], [b]) => a.localeCompare(b));
  const maxLabel = rows.reduce((max, [label, value]) => (value > (probabilities[max] ?? -1) ? label : max), rows[0]?.[0]);

  return (
    <div className="space-y-3">
      {rows.map(([label, value]) => {
        const isTop = label === (highlight ?? maxLabel);
        return (
          <div key={label}>
            <div className="mb-1.5 flex items-center justify-between text-sm">
              <span className={`font-semibold ${isTop ? 'text-clinical-modelDeep' : 'text-slate-700'}`}>{label}</span>
              <span className="font-data font-bold text-slate-950">{formatPercent(value)}</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full transition-all ${isTop ? 'bg-clinical-model' : 'bg-slate-300'}`}
                style={{ width: `${Math.max(2, Math.min(100, value * 100))}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
