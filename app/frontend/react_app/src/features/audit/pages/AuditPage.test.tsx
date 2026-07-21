import { fireEvent, render, screen, within } from '@testing-library/react';
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
        final_esi: 2,
        confidence_score: 0.7,
        safety_escalated: true,
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
            missing_fields: ['pregnancy status'],
            evidence: [{ field: 'age', value: 62, text: '62-year-old' }],
            disclaimer: 'Extracted fields require clinician review before prediction.',
            message: 'Clinical NLP extraction reviewed before ESI decision support.'
          }
        },
        {
          audit_id: 'AUD-3',
          action: 'prediction_generated',
          actor_id: 'prediction_service',
          created_at: '2026-07-14T15:00:02Z',
          details: {
            predicted_esi: 3,
            final_esi: 2,
            confidence_score: 0.7,
            latency_ms: 18,
            final_source: 'safety_rules'
          }
        },
        {
          audit_id: 'AUD-4',
          action: 'clinician_review_override',
          actor_id: 'rivera@example.test',
          created_at: '2026-07-14T15:05:00Z',
          details: {
            clinician_id: 'rivera@example.test',
            clinician_final_esi: 2,
            override_reason: 'Bedside findings required escalation.'
          }
        },
        {
          audit_id: 'AUD-5',
          action: 'report_generated',
          actor_id: 'backend_api',
          created_at: '2026-07-14T15:06:00Z',
          details: {
            report_id: 'REP-100',
            report_status: 'generated',
            include_audit: true
          }
        }
      ]
    });
  });

  it('renders event and severity filters with compact event summaries', async () => {
    render(<AuditPage />);

    expect(await screen.findByText('Assessment created')).toBeInTheDocument();
    const eventFilters = screen.getByRole('group', { name: 'Event type filters' });
    expect(within(eventFilters).getByRole('button', { name: 'All' })).toHaveAttribute('aria-pressed', 'true');
    expect(within(eventFilters).getByRole('button', { name: 'Prediction' })).toBeInTheDocument();
    expect(within(eventFilters).getByRole('button', { name: 'NLP Review' })).toBeInTheDocument();
    expect(within(eventFilters).getByRole('button', { name: 'Clinician Review' })).toBeInTheDocument();
    expect(within(eventFilters).getByRole('button', { name: 'Safety' })).toBeInTheDocument();
    expect(within(eventFilters).getByRole('button', { name: 'Report' })).toBeInTheDocument();

    const severityFilters = screen.getByRole('group', { name: 'Severity filters' });
    expect(within(severityFilters).getByRole('button', { name: 'Info' })).toBeInTheDocument();
    expect(screen.getAllByText(/Alex Morgan/)).not.toHaveLength(0);
    expect(screen.getAllByText(/Assessment AS-100/)).not.toHaveLength(0);
    expect(screen.getAllByText('Source')).not.toHaveLength(0);

    const clinicianEvent = screen.getByText('Clinician review overridden').closest('article');
    expect(clinicianEvent).not.toBeNull();
    expect(within(clinicianEvent as HTMLElement).getAllByText('rivera@example.test')).not.toHaveLength(0);
    expect(within(clinicianEvent as HTMLElement).getByText('ESI 2')).toBeInTheDocument();
    expect(within(clinicianEvent as HTMLElement).getByText('Bedside findings required escalation.')).toBeInTheDocument();

    const reportEvent = screen.getByText('PDF report generated').closest('article');
    expect(reportEvent).not.toBeNull();
    expect(within(reportEvent as HTMLElement).getByText('REP-100')).toBeInTheDocument();
    expect(within(reportEvent as HTMLElement).getByText('Generated')).toBeInTheDocument();
  });

  it('keeps NLP counts visible while long evidence is collapsed and expandable', async () => {
    render(<AuditPage />);

    const nlpTitle = await screen.findByText('Clinical NLP review completed');
    const nlpEvent = nlpTitle.closest('article');
    expect(nlpEvent).not.toBeNull();
    expect(within(nlpEvent as HTMLElement).getByText('Clinical NLP reviewed before prediction.')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('Reviewed before prediction')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('Safety cues')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('Missing fields')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('Extracted fields')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('Evidence snippets')).toBeInTheDocument();
    expect(screen.queryByText('Clinical NLP Review Evidence')).not.toBeInTheDocument();
    expect(screen.queryByText('low oxygen')).not.toBeInTheDocument();
    expect(screen.queryByText(/62-year-old/)).not.toBeInTheDocument();

    const detailsButton = within(nlpEvent as HTMLElement).getByRole('button', { name: 'View details' });
    expect(detailsButton).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(detailsButton);
    expect(within(nlpEvent as HTMLElement).getByText('Clinical NLP Review Evidence')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('low oxygen')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText('pregnancy status')).toBeInTheDocument();
    expect(within(nlpEvent as HTMLElement).getByText(/62-year-old/)).toBeInTheDocument();
    fireEvent.click(within(nlpEvent as HTMLElement).getByRole('button', { name: 'Hide details' }));
    expect(screen.queryByText('Clinical NLP Review Evidence')).not.toBeInTheDocument();
  });

  it('keeps prediction results visible without expanding details and filters by event type', async () => {
    render(<AuditPage />);

    const predictionTitle = await screen.findByText('Prediction generated');
    const predictionEvent = predictionTitle.closest('article');
    expect(predictionEvent).not.toBeNull();
    expect(within(predictionEvent as HTMLElement).getByText('ESI 3')).toBeInTheDocument();
    expect(within(predictionEvent as HTMLElement).getByText('ESI 2')).toBeInTheDocument();
    expect(within(predictionEvent as HTMLElement).getByText('Safety escalated')).toBeInTheDocument();
    expect(within(predictionEvent as HTMLElement).getByText('70.0%')).toBeInTheDocument();

    const eventFilters = screen.getByRole('group', { name: 'Event type filters' });
    fireEvent.click(within(eventFilters).getByRole('button', { name: 'NLP Review' }));
    expect(screen.getByText('Clinical NLP review completed')).toBeInTheDocument();
    expect(screen.queryByText('Prediction generated')).not.toBeInTheDocument();
    expect(screen.queryByText('Clinician review overridden')).not.toBeInTheDocument();

    fireEvent.click(within(eventFilters).getByRole('button', { name: 'Safety' }));
    expect(screen.getByText('Prediction generated')).toBeInTheDocument();
    expect(screen.queryByText('Clinical NLP review completed')).not.toBeInTheDocument();
  });
});
