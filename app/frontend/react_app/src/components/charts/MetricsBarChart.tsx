import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { ModelMetricSnapshot } from '@/types/clinical';

const METRIC_LABELS: Array<{ key: keyof ModelMetricSnapshot; label: string; invert?: boolean }> = [
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'macroF1', label: 'Macro F1' },
  { key: 'weightedF1', label: 'Weighted F1' },
  { key: 'esi5Precision', label: 'ESI 5 Precision' },
  { key: 'esi5Recall', label: 'ESI 5 Recall' },
  { key: 'esi5F1', label: 'ESI 5 F1' },
  { key: 'unsafeDowngradeRate', label: 'Unsafe 3→5', invert: true }
];

export function MetricsBarChart({ metrics }: { metrics?: ModelMetricSnapshot }) {
  const data = METRIC_LABELS.filter(({ key }) => typeof metrics?.[key] === 'number').map(({ key, label, invert }) => {
    const percent = Math.round((metrics?.[key] as number) * 1000) / 10;
    return { label, value: percent, invert: Boolean(invert) };
  });

  if (!data.length) return <p className="py-8 text-center text-sm text-slate-500">No model metrics are available yet.</p>;

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 38)}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#5B6B85' }} axisLine={false} tickLine={false} unit="%" />
        <YAxis type="category" dataKey="label" width={118} tick={{ fontSize: 12, fill: '#0B1220', fontWeight: 600 }} axisLine={false} tickLine={false} />
        <Tooltip formatter={(value) => [`${Number(value)}%`, 'Value']} contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 12 }} />
        <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={16}>
          {data.map((entry) => {
            const color = entry.invert ? (entry.value <= 1 ? '#0D9488' : entry.value <= 2 ? '#D97706' : '#DC2626') : entry.value >= 70 ? '#0D9488' : entry.value >= 50 ? '#D97706' : '#DC2626';
            return <Cell key={entry.label} fill={color} />;
          })}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
