import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { AssessmentRecord } from '@/types/clinical';
import { formatShortTime } from '@/lib/formatters';

export type OperationalTrendPoint = {
  createdAt: string;
  latencyMs?: number | null;
  confidence?: number | null;
};

export function OperationalTrendChart({
  records,
  points
}: {
  records?: AssessmentRecord[];
  points?: OperationalTrendPoint[];
}) {
  const source = points ?? records?.map((record) => ({
    createdAt: record.prediction.createdAt,
    latencyMs: record.prediction.latencyMs,
    confidence: record.prediction.confidence
  })) ?? [];

  const data = [...source]
    .sort((a, b) => +new Date(a.createdAt) - +new Date(b.createdAt))
    .slice(-12)
    .map((point) => ({
      label: formatShortTime(point.createdAt),
      latency: typeof point.latencyMs === 'number' ? point.latencyMs : null,
      confidence: typeof point.confidence === 'number' ? Math.round(point.confidence * 100) : null
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
          formatter={(value, name) => {
            if (name === 'latency') return [value === null ? 'N/A' : `${Number(value)} ms`, 'Latency'];
            return [value === null ? 'N/A' : `${Number(value)}%`, 'Confidence'];
          }}
        />
        <Bar yAxisId="latency" dataKey="latency" fill="#CBD5E1" radius={[6, 6, 0, 0]} barSize={18} />
        <Line yAxisId="confidence" type="monotone" dataKey="confidence" stroke="#0D9488" strokeWidth={2.5} dot={{ r: 3, fill: '#0D9488' }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
