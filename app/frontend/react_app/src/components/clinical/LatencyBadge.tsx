import { latencyTier, tierTone } from '@/lib/formatters';

export function LatencyBadge({ ms, size = 'md' }: { ms: number; size?: 'sm' | 'md' }) {
  const tier = latencyTier(ms);
  const tone = tierTone(tier);
  const padding = size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-sm';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-data font-semibold ${tone.border} ${tone.bg} ${tone.text} ${padding}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${tone.dot}`} />
      {ms} ms
    </span>
  );
}
