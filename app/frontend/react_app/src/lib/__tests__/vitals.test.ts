import { describe, expect, it } from 'vitest';
import { ageBand, bloodPressureFlag, vitalFlag, watchVitalCount } from '@/lib/vitals';

describe('age-aware vital display flags', () => {
  it('uses pediatric ranges instead of adult-only ranges', () => {
    expect(ageBand(3)).toBe('toddler');
    expect(vitalFlag('heartRate', 138, 3)).toBe('normal');
    expect(vitalFlag('heartRate', 138, 32)).toBe('critical');
  });

  it('flags low oxygen saturation as critical', () => {
    expect(vitalFlag('spo2', 89, 64)).toBe('critical');
  });

  it('shows 92/60 blood pressure outside the adult display range', () => {
    expect(bloodPressureFlag({
      heartRate: 118,
      respiratoryRate: 22,
      systolicBp: 92,
      diastolicBp: 60,
      temperatureC: 38.2,
      spo2: 91,
      painScore: 5
    }, 62)).toBe('abnormal');
  });

  it('counts the six displayed vital cards without double-counting blood pressure', () => {
    expect(watchVitalCount({
      heartRate: 118,
      respiratoryRate: 22,
      systolicBp: 92,
      diastolicBp: 60,
      temperatureC: 38.2,
      spo2: 91,
      painScore: 5
    }, 62)).toBe(5);
  });
});
