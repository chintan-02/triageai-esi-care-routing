import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS: Record<string, string> = {
  'ESI 1': '#7F1D1D',
  'ESI 2': '#DC2626',
  'ESI 3': '#D97706',
  'ESI 4': '#2563EB',
  'ESI 5': '#16A34A'
};

const LEGEND_COPY: Record<string, string> = {
  'ESI 1': 'High acuity',
  'ESI 2': 'High acuity',
  'ESI 3': 'Urgent',
  'ESI 4': 'Less urgent',
  'ESI 5': 'Non-urgent'
};

export function EsiDistributionDonut({ distribution }: { distribution: Record<string, number> }) {
  const data = Object.entries(distribution)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, value]) => ({ name, value }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (!total) {
    return <p className="py-8 text-center text-sm text-slate-500">No assessments recorded yet.</p>;
  }

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center">
      <div className="relative h-[168px] w-[168px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={78} paddingAngle={2} stroke="#ffffff" strokeWidth={2}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name] ?? '#94A3B8'} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value, name) => {
                const numeric = Number(value);
                return [`${numeric} (${((numeric / total) * 100).toFixed(0)}%)`, String(name)];
              }}
              contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 12 }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="font-data text-2xl font-extrabold text-slate-950">{total}</p>
          <p className="text-[11px] font-semibold text-slate-500">total</p>
        </div>
      </div>
      <div className="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-1">
        {data.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm">
            <div className="flex min-w-0 items-center gap-2 font-semibold text-slate-700">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[entry.name] ?? '#94A3B8' }} />
              <span className="truncate">{entry.name} · {LEGEND_COPY[entry.name] ?? 'Final routing'}</span>
            </div>
            <span className="font-data font-bold text-slate-950">{entry.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
