import { describe, expect, it } from 'vitest';
import { deriveWorkflowStatus } from '@/lib/workflowStatus';

describe('deriveWorkflowStatus', () => {
  it.each([
    {
      input: {
        requiredIntakeComplete: false,
        nlpState: 'not-used' as const,
        hasUndocumentedInformation: true
      },
      label: 'Required intake incomplete',
      enabled: false
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'review-required' as const,
        hasUndocumentedInformation: true
      },
      label: 'NLP review confirmation required',
      enabled: false
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'stale' as const,
        hasUndocumentedInformation: true
      },
      label: 'NLP extraction stale',
      enabled: false
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'reviewed' as const,
        hasUndocumentedInformation: true
      },
      label: 'Ready with undocumented intake information',
      enabled: true
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'not-used' as const,
        hasUndocumentedInformation: false
      },
      label: 'Ready for prediction',
      enabled: true
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'reviewed' as const,
        hasUndocumentedInformation: false,
        clinicianReviewState: 'required' as const
      },
      label: 'Clinician review required',
      enabled: false
    },
    {
      input: {
        requiredIntakeComplete: true,
        nlpState: 'reviewed' as const,
        hasUndocumentedInformation: false,
        clinicianReviewState: 'accepted' as const
      },
      label: 'Clinician review accepted',
      enabled: false
    }
  ])('returns $label without contradictory prediction enablement', ({ input, label, enabled }) => {
    expect(deriveWorkflowStatus(input)).toEqual(
      expect.objectContaining({
        label,
        predictionEnabled: enabled
      })
    );
  });
});
