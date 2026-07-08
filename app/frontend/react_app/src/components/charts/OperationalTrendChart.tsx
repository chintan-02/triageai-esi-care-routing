import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { AssessmentRecord } from '@/types/clinical';
import { formatShortTime } from '@/lib/formatters';

export function OperationalTrendChart({ records }: { records: AssessmentRecord[] }) {
  const data = [...records]
    .sort((a, b) => +new Date(a.prediction.createdAt) - +new Date(b.prediction.createdAt))
    .slice(-12)
    .map((record) => ({
      label: formatShortTime(record.prediction.createdAt),
      latency: record.prediction.latencyMs,
      confidence: Math.round(record.prediction.confidence * 100)
    }));

  if (data.length < 2) {
    return <p className="py-8 text-center text-sm text-slate-500">Not enough assessments yet to chart a trend.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#5B6B85' }} axisLine={{ stroke: '#E2E8F0' }} tickLine={false} />
        <YAxis yAxisId="latency" tick={{ fontSize: 11, fill: '#5B6B85' }} axisLine={false} tickLine={false} width={44} />
        <YAxis yAxisId="confidence" orientation="right" domain={[0, 100]} tick={{ fontSize: 11, fill: '#5B6B85' }} axisLine={false} tickLine={false} width={34} />
        <Tooltip
          contentStyle={{ borderRadius: 12, border: '1px solid #E2E8F0', fontSize: 12 }}
          formatter={(value, name) => (name === 'latency' ? [`${Number(value)} ms`, 'Latency'] : [`${Number(value)}%`, 'Confidence'])}
        />
        <Bar yAxisId="latency" dataKey="latency" fill="#CBD5E1" radius={[6, 6, 0, 0]} barSize={18} />
        <Line yAxisId="confidence" type="monotone" dataKey="confidence" stroke="#0D9488" strokeWidth={2.5} dot={{ r: 3, fill: '#0D9488' }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
