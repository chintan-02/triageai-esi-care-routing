import type { Vitals } from '@/types/clinical';

export type VitalKey = keyof Vitals;
export type VitalFlag = 'normal' | 'abnormal' | 'critical';
export type AgeBand = 'infant' | 'toddler' | 'child' | 'adolescent' | 'adult';

interface VitalRange {
  criticalLow?: number;
  low?: number;
  high?: number;
  criticalHigh?: number;
}

const ADULT_RANGES: Record<VitalKey, VitalRange> = {
  heartRate: { criticalLow: 40, low: 60, high: 100, criticalHigh: 130 },
  respiratoryRate: { criticalLow: 8, low: 12, high: 20, criticalHigh: 28 },
  systolicBp: { criticalLow: 85, low: 90, high: 140, criticalHigh: 180 },
  diastolicBp: { criticalLow: 45, low: 60, high: 90, criticalHigh: 110 },
  temperatureC: { criticalLow: 35, low: 36.1, high: 38, criticalHigh: 39.5 },
  spo2: { criticalLow: 90, low: 94, criticalHigh: 101 },
  painScore: { high: 6, criticalHigh: 8 }
};

const PEDIATRIC_RANGES: Record<AgeBand, Partial<Record<VitalKey, VitalRange>>> = {
  infant: {
    heartRate: { criticalLow: 80, low: 100, high: 160, criticalHigh: 190 },
    respiratoryRate: { criticalLow: 20, low: 30, high: 60, criticalHigh: 70 },
    systolicBp: { criticalLow: 65, low: 70, high: 110, criticalHigh: 130 },
    diastolicBp: { criticalLow: 35, low: 45, high: 70, criticalHigh: 85 }
  },
  toddler: {
    heartRate: { criticalLow: 70, low: 90, high: 150, criticalHigh: 180 },
    respiratoryRate: { criticalLow: 16, low: 22, high: 40, criticalHigh: 55 },
    systolicBp: { criticalLow: 70, low: 80, high: 115, criticalHigh: 135 },
    diastolicBp: { criticalLow: 35, low: 45, high: 75, criticalHigh: 90 }
  },
  child: {
    heartRate: { criticalLow: 55, low: 70, high: 120, criticalHigh: 160 },
    respiratoryRate: { criticalLow: 12, low: 18, high: 30, criticalHigh: 42 },
    systolicBp: { criticalLow: 75, low: 85, high: 125, criticalHigh: 145 },
    diastolicBp: { criticalLow: 40, low: 50, high: 80, criticalHigh: 95 }
  },
  adolescent: {
    heartRate: { criticalLow: 45, low: 60, high: 105, criticalHigh: 145 },
    respiratoryRate: { criticalLow: 9, low: 12, high: 22, criticalHigh: 32 },
    systolicBp: { criticalLow: 80, low: 90, high: 135, criticalHigh: 170 },
    diastolicBp: { criticalLow: 45, low: 55, high: 85, criticalHigh: 105 }
  },
  adult: ADULT_RANGES
};

export function ageBand(age?: number): AgeBand {
  if (typeof age !== 'number' || Number.isNaN(age)) return 'adult';
  if (age < 1) return 'infant';
  if (age < 5) return 'toddler';
  if (age < 13) return 'child';
  if (age < 18) return 'adolescent';
  return 'adult';
}

export function vitalRange(key: VitalKey, age?: number): VitalRange {
  const band = ageBand(age);
  return PEDIATRIC_RANGES[band][key] ?? ADULT_RANGES[key];
}

export function vitalFlag(key: VitalKey, value: number, age?: number): VitalFlag {
  const range = vitalRange(key, age);
  if (!range) return 'normal';
  if (range.criticalLow !== undefined && value < range.criticalLow) return 'critical';
  if (range.criticalHigh !== undefined && value >= range.criticalHigh) return 'critical';
  if (range.low !== undefined && value < range.low) return 'abnormal';
  if (range.high !== undefined && value > range.high) return 'abnormal';
  return 'normal';
}

export function vitalFlagTone(flag: VitalFlag) {
  switch (flag) {
    case 'critical':
      return 'border-red-300 bg-red-50 text-red-800';
    case 'abnormal':
      return 'border-amber-300 bg-amber-50 text-amber-800';
    default:
      return 'border-slate-200 bg-slate-50 text-slate-950';
  }
}

export function vitalStatusLabel(flag: VitalFlag) {
  switch (flag) {
    case 'critical':
      return 'Critical';
    case 'abnormal':
      return 'Watch';
    default:
      return 'In range';
  }
}
