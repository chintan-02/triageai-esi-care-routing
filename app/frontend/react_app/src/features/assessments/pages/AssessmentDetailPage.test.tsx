import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { AssessmentDetail } from '@/types/api';
import { AssessmentDetailPage } from './AssessmentDetailPage';

const { getAssessment, downloadAssessmentPdf, submitClinicianReview } = vi.hoisted(() => ({
  getAssessment: vi.fn(),
  downloadAssessmentPdf: vi.fn(),
  submitClinicianReview: vi.fn()
}));

vi.mock('@/api/assessments', () => ({
  getAssessment,
  downloadAssessmentPdf
}));

vi.mock('@/api/reviews', () => ({
  submitClinicianReview
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: { name: 'Dr. Rivera', email: 'rivera@example.test', role: 'Doctor' }
  })
}));

vi.mock('@/context/ToastContext', () => ({
  useToast: () => ({ showToast: vi.fn() })
}));

function assessmentDetail(): AssessmentDetail {
  return {
    request_id: 'REQ-1',
    assessment_id: 'AS-100',
    patient_id: 'PAT-100',
    patient_name: 'Alex Morgan',
    mrn: 'MRN-100',
    age: 62,
    sex: 'male',
    arrival_mode: 'Walk-in',
    status: 'pending_review',
    chief_complaint: 'Chest pain',
    symptom_duration: '2 hours',
    symptom_narrative: 'Structured symptom narrative.',
    pain_score: 6,
    temperature_c: 38.2,
    heart_rate: 118,
    respiratory_rate: 20,
    systolic_bp: 92,
    diastolic_bp: 60,
    oxygen_saturation: 91,
    vitals: {},
    risk_flags: [],
    comorbidities: [],
    final_esi: 2,
    model_predicted_esi: 3,
    safety_escalated: true,
    probabilities: { ESI_3: 0.7, ESI_4: 0.2, ESI_5: 0.1 },
    confidence: 0.7,
    review_status: 'pending',
    review_status_normalized: 'pending',
    created_at: '2026-07-14T15:00:00Z',
    latest_prediction: {
      prediction_id: 'PRED-1',
      model_version: 'lightgbm_v2_weight_threshold_esi345',
      model_loaded: true,
      predicted_esi: 3,
      final_esi: 2,
      confidence_score: 0.7,
      latency_ms: 18,
      probabilities: { ESI_3: 0.7, ESI_4: 0.2, ESI_5: 0.1 },
      safety_rules_triggered: [
        {
          rule_id: 'low_oxygen_saturation',
          triggered: true,
          message: 'Oxygen saturation 91% requires safety-rule escalation.',
          severity: 'critical',
          escalates_to: 2
        },
        {
          rule_id: 'chest_pain_shortness_of_breath',
          triggered: true,
          message: 'Chest pain with shortness of breath requires urgent clinician review.',
          severity: 'high',
          escalates_to: 2
        }
      ],
      final_source: 'safety_rules',
      recommendation: 'Clinician review is required.',
      explanation: 'Decision-support output available for review.',
      clinician_summary: 'Structured assessment summary.',
      is_placeholder: false,
      created_at: '2026-07-14T15:00:01Z'
    },
    latest_clinician_review: null,
    audit_trail: [
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
        created_at: '2026-07-14T15:00:00Z',
        details: {
          reviewed: true,
          source: 'clinical_intake_nlp',
          extracted_fields: {
            age: 62,
            gender: 'Male',
            chief_complaint: 'chest pain',
            symptoms: ['chest pain', 'shortness of breath'],
            vitals: { hr: 118, sbp: 92, dbp: 60, rr: 20, o2: 91, temp: 38.2 },
            raw_note: 'PRIVATE RAW NOTE MUST NOT APPEAR'
          },
          safety_cues: ['low oxygen', 'low blood pressure'],
          missing_fields: ['pregnancy status'],
          evidence: [
            { field: 'age', value: 62, text: '62-year-old' },
            { field: 'triage_vital_hr', value: 118, text: 'HR 118' }
          ],
          disclaimer: 'Extracted fields require clinician review before prediction.',
          message: 'Clinical NLP extraction reviewed before ESI decision support.',
          raw_note: 'PRIVATE RAW NOTE MUST NOT APPEAR'
        }
      },
      {
        audit_id: 'AUD-3',
        action: 'prediction_generated',
        actor_id: 'prediction_service',
        created_at: '2026-07-14T15:00:01Z',
        details: { predicted_esi: 3, final_esi: 2 }
      },
      {
        audit_id: 'AUD-4',
        action: 'clinician_review_accept',
        actor_id: 'rivera@example.test',
        created_at: '2026-07-14T15:05:00Z',
        details: { clinician_final_esi: 2, clinician_id: 'rivera@example.test' }
      }
    ],
    report_ids: [],
    message: 'Assessment loaded from database.',
    is_placeholder: false
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/assessments/AS-100']}>
      <Routes>
        <Route path="/assessments/:id" element={<AssessmentDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('AssessmentDetailPage', () => {
  beforeEach(() => {
    getAssessment.mockReset();
    getAssessment.mockResolvedValue(assessmentDetail());
    downloadAssessmentPdf.mockReset();
    submitClinicianReview.mockReset();
    submitClinicianReview.mockResolvedValue({});
  });

  it('renders final decision, full-width clinical sign-off, then the tabbed review workspace', async () => {
    renderPage();

    const overviewTab = await screen.findByRole('tab', { name: 'Overview' });
    expect(overviewTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'Intake' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Model & Safety' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'NLP Evidence' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Audit Trail' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Report' })).toBeInTheDocument();

    expect(screen.getByText('Final routing decision')).toBeInTheDocument();
    const signOffHeading = screen.getByRole('heading', { name: 'Clinical Review / Sign-off' });
    const signOffCard = signOffHeading.closest('section');
    const tabList = screen.getByRole('tablist', { name: 'Assessment review sections' });
    expect(signOffCard).not.toBeNull();
    expect(signOffHeading.compareDocumentPosition(tabList) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(signOffCard as HTMLElement).getByText('Current reviewer')).toBeInTheDocument();
    expect(within(signOffCard as HTMLElement).getByText('Review status')).toBeInTheDocument();
    expect(within(signOffCard as HTMLElement).getByLabelText('Final clinician decision')).toBeInTheDocument();
    expect(within(signOffCard as HTMLElement).getByLabelText('Review note / override reason')).toBeInTheDocument();
    expect(within(signOffCard as HTMLElement).getByText('Decision support only. Clinician judgment remains required for final routing.')).toBeInTheDocument();
    expect(screen.getByText('Why the final ESI changed')).toBeInTheDocument();
    const acuityCard = screen.getByText('Acuity routing').closest('section');
    expect(acuityCard).not.toBeNull();
    expect(within(acuityCard as HTMLElement).getByRole('img', { name: 'Acuity gauge showing final ESI 2' })).toBeInTheDocument();
    expect(within(acuityCard as HTMLElement).getByText('Emergent')).toBeInTheDocument();
    expect(within(acuityCard as HTMLElement).getByText('Escalated from model prediction ESI 3')).toBeInTheDocument();
    expect(within(acuityCard as HTMLElement).getByText('70.0%')).toBeInTheDocument();
    expect(within(acuityCard as HTMLElement).getByText('18 ms')).toBeInTheDocument();
    expect(within(acuityCard as HTMLElement).getByText('Pending review')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Accept' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Override' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Generate PDF' })).toBeEnabled();

    fireEvent.click(screen.getByRole('tab', { name: 'Intake' }));
    expect(screen.getByText('Patient intake')).toBeInTheDocument();
    expect(screen.getByText('MRN-100')).toBeInTheDocument();
    expect(screen.getByText('Structured symptom narrative.')).toBeInTheDocument();
    expect(screen.getByText('Final routing decision')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Clinical Review / Sign-off' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Model & Safety' }));
    expect(screen.getByRole('heading', { name: 'Model output' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Safety rules' })).toBeInTheDocument();
    expect(screen.getByText('Class probabilities')).toBeInTheDocument();
    expect(screen.getByText('Model family/version')).toBeInTheDocument();
    expect(screen.getByText('Threshold profile')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Model explanation' })).toBeInTheDocument();
    expect(screen.getAllByText('Oxygen saturation 91% requires safety-rule escalation.').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Chest pain with shortness of breath requires urgent clinician review.').length).toBeGreaterThan(0);
    expect(screen.getByText('critical')).toBeInTheDocument();
    expect(screen.getByText('high')).toBeInTheDocument();
    expect(screen.getAllByText('Escalates to ESI 2')).toHaveLength(2);
    expect(screen.queryByRole('img', { name: /acuity gauge/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Routing outcome')).not.toBeInTheDocument();
    expect(screen.queryByText('Acuity routing')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Report' }));
    expect(screen.getByText('PDF decision-support report')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Generate PDF Report' })).toBeEnabled();
    expect(screen.getByText(/not a substitute for clinician judgment/i)).toBeInTheDocument();
  });

  it('shows reviewed NLP evidence with snippets collapsed by default and excludes raw note metadata', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('tab', { name: 'NLP Evidence' }));
    expect(await screen.findByText('Clinical NLP Review Evidence')).toBeInTheDocument();
    expect(screen.getByText('Reviewed before prediction')).toBeInTheDocument();
    expect(screen.getByText('low oxygen')).toBeInTheDocument();
    expect(screen.getByText('low blood pressure')).toBeInTheDocument();
    expect(screen.getByText('pregnancy status')).toBeInTheDocument();
    expect(screen.getByText('HR')).toBeInTheDocument();
    expect(screen.getByText('118')).toBeInTheDocument();
    expect(screen.queryByText(/62-year-old/)).not.toBeInTheDocument();

    const evidenceButton = screen.getByRole('button', { name: 'View evidence snippets (2)' });
    expect(evidenceButton).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(evidenceButton);
    expect(screen.getByText(/62-year-old/)).toBeInTheDocument();
    const hideEvidenceButton = screen.getByRole('button', { name: 'Hide evidence snippets' });
    expect(hideEvidenceButton).toHaveAttribute('aria-expanded', 'true');
    fireEvent.click(hideEvidenceButton);
    expect(screen.queryByText(/62-year-old/)).not.toBeInTheDocument();
    expect(screen.queryByText('PRIVATE RAW NOTE MUST NOT APPEAR')).not.toBeInTheDocument();
  });

  it('keeps assessment, NLP, prediction, and clinician review events in the Audit Trail tab', async () => {
    renderPage();

    fireEvent.click(await screen.findByRole('tab', { name: 'Audit Trail' }));
    expect(screen.getByText('Assessment created')).toBeInTheDocument();
    expect(
      screen.getByText('Assessment created and queued for clinician review.')
    ).toBeInTheDocument();
    expect(screen.getByText('NLP extraction reviewed')).toBeInTheDocument();
    expect(screen.getByText('Prediction generated')).toBeInTheDocument();
    expect(screen.getByText('Clinician review accepted')).toBeInTheDocument();
    expect(screen.queryByText('Clinical NLP Review Evidence')).not.toBeInTheDocument();
  });

  it('keeps the clinician accept workflow usable alongside every tab', async () => {
    renderPage();

    await screen.findByRole('tab', { name: 'Overview' });
    fireEvent.click(screen.getByRole('tab', { name: 'Audit Trail' }));
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));

    await waitFor(() => {
      expect(submitClinicianReview).toHaveBeenCalledWith({
        assessment_id: 'AS-100',
        clinician_id: 'rivera@example.test',
        action: 'accept',
        final_esi: 2,
        override_reason: null,
        notes: 'Current final routing decision accepted.'
      });
    });
  });
});
