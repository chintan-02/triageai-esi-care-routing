import type { EsiLevel, RiskSeverity } from '@/types/clinical';

export const riskLabelForEsi = (level: EsiLevel) => {
  if (level <= 2) return 'High Acuity';
  if (level === 3) return 'Urgent Review';
  if (level === 4) return 'Lower Acuity';
  return 'Fast Track';
};

export const severityRank = (severity: RiskSeverity) => {
  const ranks: Record<RiskSeverity, number> = {
    low: 1,
    moderate: 2,
    high: 3,
    critical: 4
  };
  return ranks[severity];
};
