import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuditPage } from './AuditPage';

const { listAssessments, getAssessmentAudit } = vi.hoisted(() => ({
  listAssessments: vi.fn(),
  getAssessmentAudit: vi.fn()
}));

vi.mock('@/api/assessments', () => ({
  listAssessments,
  getAssessmentAudit
}));

describe('AuditPage', () => {
  beforeEach(() => {
    listAssessments.mockReset();
    getAssessmentAudit.mockReset();
    listAssessments.mockResolvedValue([
      {
        assessment_id: 'AS-100',
        patient_name: 'Alex Morgan',
        mrn: 'MRN-100',
        model_predicted_esi: 3,
        final_esi: 3,
        safety_escalated: false,
        created_at: '2026-07-14T15:00:00Z',
        report_ids: []
      }
    ]);
    getAssessmentAudit.mockResolvedValue({
      assessment_id: 'AS-100',
      events: [
        {
          audit_id: 'AUD-1',
          action: 'assessment_created',
          actor_id: 'backend_api',
          created_at: '2026-07-14T15:00:00Z',
          details: { message: 'Assessment created and queued for clinician review.' }
        },
        {
          audit_id: 'AUD-2',
          action: 'nlp_extraction_reviewed',
          actor_id: 'clinical_nlp_review_ui',
          created_at: '2026-07-14T15:00:01Z',
          details: {
            extracted_fields: { age: 62 },
            safety_cues: ['low oxygen'],
            missing_fields: [],
            evidence: [{ field: 'age', value: 62, text: '62-year-old' }],
            disclaimer: 'Extracted fields require clinician review before prediction.',
            message: 'Clinical NLP extraction reviewed before ESI decision support.'
          }
        }
      ]
    });
  });

  it('keeps existing audit cards and adds reviewed NLP evidence', async () => {
    render(<AuditPage />);

    expect(await screen.findByText('Assessment created')).toBeInTheDocument();
    expect(screen.getByText('Clinical NLP Review Evidence')).toBeInTheDocument();
    expect(screen.getByText('low oxygen')).toBeInTheDocument();
    expect(screen.getByText(/62-year-old/)).toBeInTheDocument();
  });
});
