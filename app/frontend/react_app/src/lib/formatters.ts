import type { EsiLevel, RiskSeverity } from '@/types/clinical';

export const formatPercent = (value?: number) => {
  if (typeof value !== 'number' || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(1)}%`;
};

export const formatDateTime = (iso: string) => {
  const date = new Date(iso);
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

export const formatShortTime = (iso: string) => {
  const date = new Date(iso);
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(date);
};

export const formatShortDate = (iso: string) => {
  const date = new Date(iso);
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: '2-digit' }).format(date);
};

export const esiLabel = (level: EsiLevel) => `ESI ${level}`;

export const esiDescriptor = (level: EsiLevel) => {
  switch (level) {
    case 1:
      return 'Resuscitation';
    case 2:
      return 'Emergent';
    case 3:
      return 'Urgent';
    case 4:
      return 'Less urgent';
    default:
      return 'Non-urgent';
  }
};

/**
 * Solid, high-contrast acuity colors (white text on a saturated fill).
 * ESI is the one signal that must be scannable at a glance across a busy
 * queue, so it intentionally reads louder than secondary metadata chips.
 */
export const esiSolidTone = (level: EsiLevel) => {
  const tones: Record<EsiLevel, string> = {
    1: 'bg-acuity-1 text-white border-acuity-1',
    2: 'bg-acuity-2 text-white border-acuity-2',
    3: 'bg-acuity-3 text-white border-acuity-3',
    4: 'bg-acuity-4 text-white border-acuity-4',
    5: 'bg-acuity-5 text-white border-acuity-5'
  };
  return tones[level];
};

export const esiTextTone = (level: EsiLevel) => {
  const tones: Record<EsiLevel, string> = {
    1: 'text-acuity-1',
    2: 'text-acuity-2',
    3: 'text-acuity-3',
    4: 'text-acuity-4',
    5: 'text-acuity-5'
  };
  return tones[level];
};

export const severityTone = (severity: RiskSeverity) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-950 text-white border-red-950';
    case 'high':
      return 'bg-red-50 text-red-800 border-red-200';
    case 'moderate':
      return 'bg-amber-50 text-amber-800 border-amber-200';
    case 'low':
    default:
      return 'bg-slate-100 text-slate-700 border-slate-300';
  }
};

export type SignalTier = 'good' | 'watch' | 'poor';

/** Latency tiers tuned for a real-time inference endpoint (p50 target < 150ms). */
export const latencyTier = (ms: number): SignalTier => {
  if (ms < 150) return 'good';
  if (ms < 400) return 'watch';
  return 'poor';
};

export const confidenceTier = (value: number): SignalTier => {
  if (value >= 0.75) return 'good';
  if (value >= 0.5) return 'watch';
  return 'poor';
};

export const tierTone = (tier: SignalTier) => {
  switch (tier) {
    case 'good':
      return { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', dot: 'bg-emerald-500' };
    case 'watch':
      return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-500' };
    default:
      return { text: 'text-red-700', bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500' };
  }
};

export const getInitials = (name: string) =>
  name
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
