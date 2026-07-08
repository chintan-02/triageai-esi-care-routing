import { describe, expect, it } from 'vitest';
import { formatPercent } from '@/lib/formatters';

describe('formatPercent', () => {
  it('formats valid percentages and safely handles missing values', () => {
    expect(formatPercent(0.7832)).toBe('78.3%');
    expect(formatPercent(undefined)).toBe('—');
    expect(formatPercent(Number.NaN)).toBe('—');
  });
});
