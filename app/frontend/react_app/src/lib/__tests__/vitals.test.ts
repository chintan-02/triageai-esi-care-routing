import { describe, expect, it } from 'vitest';
import { ageBand, vitalFlag } from '@/lib/vitals';

describe('age-aware vital display flags', () => {
  it('uses pediatric ranges instead of adult-only ranges', () => {
    expect(ageBand(3)).toBe('toddler');
    expect(vitalFlag('heartRate', 138, 3)).toBe('normal');
    expect(vitalFlag('heartRate', 138, 32)).toBe('critical');
  });

  it('flags low oxygen saturation as critical', () => {
    expect(vitalFlag('spo2', 89, 64)).toBe('critical');
  });
});
