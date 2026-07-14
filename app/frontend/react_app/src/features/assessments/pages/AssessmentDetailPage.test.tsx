import { render, screen } from '@testing-library/react';
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
    final_esi: 3,
    model_predicted_esi: 3,
    safety_escalated: false,
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
      final_esi: 3,
      confidence_score: 0.7,
      latency_ms: 18,
      probabilities: { ESI_3: 0.7, ESI_4: 0.2, ESI_5: 0.1 },
      safety_rules_triggered: [],
      final_source: 'model',
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
  });

  it('renders reviewed Clinical NLP evidence without raw note metadata', async () => {
    renderPage();

    expect(await screen.findByText('Clinical NLP Review Evidence')).toBeInTheDocument();
    expect(screen.getByText('Reviewed before prediction')).toBeInTheDocument();
    expect(screen.getByText('low oxygen')).toBeInTheDocument();
    expect(screen.getByText('low blood pressure')).toBeInTheDocument();
    expect(screen.getByText('pregnancy status')).toBeInTheDocument();
    expect(screen.getByText(/HR 118/)).toBeInTheDocument();
    expect(screen.getByText(/62-year-old/)).toBeInTheDocument();
    expect(screen.queryByText('PRIVATE RAW NOTE MUST NOT APPEAR')).not.toBeInTheDocument();
  });

  it('keeps generic audit events visible', async () => {
    renderPage();

    expect(await screen.findByText('Assessment created')).toBeInTheDocument();
    expect(
      screen.getByText('Assessment created and queued for clinician review.')
    ).toBeInTheDocument();
  });
});
