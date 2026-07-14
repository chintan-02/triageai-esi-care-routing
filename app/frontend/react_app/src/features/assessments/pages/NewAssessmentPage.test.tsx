import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NewAssessmentPage } from './NewAssessmentPage';

const { createPrediction, extractClinicalIntake } = vi.hoisted(() => ({
  createPrediction: vi.fn(),
  extractClinicalIntake: vi.fn()
}));
const showToast = vi.fn();
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

vi.mock('@/api/predictions', () => ({
  createPrediction
}));

vi.mock('@/api/clinicalNlp', () => ({
  extractClinicalIntake
}));

vi.mock('@/context/ToastContext', () => ({
  useToast: () => ({ showToast })
}));

describe('NewAssessmentPage', () => {
  it('fills the clinical note with the demo scenario without running extraction or prediction', () => {
    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'Alex Morgan' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /use demo note/i }));

    expect(screen.getByLabelText(/clinical note \/ transcript/i)).toHaveValue(
      '62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.'
    );
    expect(screen.getByText('Demo note is for workflow testing only.')).toBeInTheDocument();
    expect(extractClinicalIntake).not.toHaveBeenCalled();
    expect(createPrediction).not.toHaveBeenCalled();
  });

  it('clears stale NLP extraction review state when loading the demo note', async () => {
    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'Alex Morgan' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.change(screen.getByLabelText(/clinical note \/ transcript/i), {
      target: { value: 'Previous note for extraction.' }
    });
    fireEvent.click(screen.getByRole('button', { name: /extract intake fields/i }));

    await screen.findByText(/clinical intake nlp safety layer/i);
    fireEvent.click(
      screen.getByRole('checkbox', {
        name: /i reviewed the extracted fields before prediction/i
      })
    );
    fireEvent.click(screen.getByRole('button', { name: /use demo note/i }));

    expect(screen.queryByText(/clinical intake nlp safety layer/i)).not.toBeInTheDocument();
    expect(
      screen.queryByRole('checkbox', {
        name: /i reviewed the extracted fields before prediction/i
      })
    ).not.toBeInTheDocument();
    expect(extractClinicalIntake).toHaveBeenCalledTimes(1);
    expect(createPrediction).not.toHaveBeenCalled();
  });

  it('extracts clinical note fields for clinician review without running prediction', async () => {
  render(
    <MemoryRouter>
      <NewAssessmentPage />
    </MemoryRouter>
  );

  fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'Alex Morgan' } });

  const nextButton = screen.getByRole('button', { name: /next/i });
  fireEvent.click(nextButton);

  const note =
    '62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2.';

  fireEvent.change(screen.getByLabelText(/clinical note \/ transcript/i), {
    target: { value: note }
  });

  fireEvent.click(screen.getByRole('button', { name: /extract intake fields/i }));

  await waitFor(() => {
    expect(extractClinicalIntake).toHaveBeenCalledWith(note);
  });

  expect(screen.getByText(/clinical intake nlp safety layer/i)).toBeInTheDocument();
  expect(screen.getAllByText(/low oxygen/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/low blood pressure/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/respiratory rate/i).length).toBeGreaterThan(0);

  fireEvent.click(screen.getByRole('button', { name: /patient/i }));

  expect((screen.getByLabelText(/age/i) as HTMLInputElement).value).toBe('62');
  expect((screen.getByLabelText(/sex/i) as HTMLSelectElement).value).toBe('Male');

  fireEvent.click(screen.getByRole('button', { name: /complaint/i }));

  expect((screen.getByLabelText(/chief complaint/i) as HTMLInputElement).value).toBe('chest pain');
  expect((screen.getByLabelText(/symptom narrative/i) as HTMLTextAreaElement).value).toBe(note);

  expect(createPrediction).not.toHaveBeenCalled();
});
  beforeEach(() => {
    extractClinicalIntake.mockReset();
extractClinicalIntake.mockResolvedValue({
  age: 62,
  gender: 'Male',
  chief_complaint: 'chest pain',
  symptoms: ['chest pain', 'shortness of breath'],
  vitals: {
    hr: 118,
    sbp: 92,
    dbp: 60,
    rr: null,
    o2: 91,
    temp: 38.2
  },
  safety_cues: ['chest pain', 'shortness of breath', 'low oxygen', 'low blood pressure', 'tachycardia'],
  missing_fields: ['respiratory rate'],
  evidence: [
    { field: 'age', value: 62, text: '62-year-old' },
    { field: 'triage_vital_hr', value: 118, text: 'HR 118' },
    { field: 'triage_vital_sbp', value: 92, text: 'BP 92/60' },
    { field: 'triage_vital_o2', value: 91, text: 'O2 91%' }
  ],
  requires_clinician_review: true,
  disclaimer: 'Decision support only. Extracted fields require clinician review before prediction.'
});
    createPrediction.mockReset();
    showToast.mockReset();
    mockNavigate.mockReset();
    createPrediction.mockResolvedValue({
      assessment_id: 'AS-100',
      final_esi: 3
    });
  });

  it('shows the review step with a clear decision-support CTA', () => {
    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    const patientNameInput = screen.getByLabelText(/patient name/i);
    fireEvent.change(patientNameInput, { target: { value: 'Alex Morgan' } });

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    const chiefComplaintInput = screen.getByLabelText(/chief complaint/i);
    fireEvent.change(chiefComplaintInput, { target: { value: 'Chest pain' } });

    const symptomNarrative = screen.getByLabelText(/symptom narrative/i);
    fireEvent.change(symptomNarrative, { target: { value: 'Sharp pain with dizziness' } });

    const durationInput = screen.getByLabelText(/duration/i);
    fireEvent.change(durationInput, { target: { value: '2 hours' } });

    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    expect(screen.getByText(/safety gate preview/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run esi decision support/i })).toBeInTheDocument();
    expect(createPrediction).not.toHaveBeenCalled();
  });

  it('preserves intake state on review and only submits from the final CTA', async () => {
    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'harsh' } });
    fireEvent.change(screen.getByLabelText(/sex/i), { target: { value: 'Female' } });
    fireEvent.change(screen.getByLabelText(/arrival mode/i), { target: { value: 'Ambulance' } });

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);

    fireEvent.change(screen.getByLabelText(/chief complaint/i), { target: { value: 'pain' } });
    fireEvent.change(screen.getByLabelText(/symptom narrative/i), { target: { value: 'brief' } });
    fireEvent.change(screen.getByLabelText(/duration/i), { target: { value: '1' } });

    fireEvent.click(nextButton);
    fireEvent.change(screen.getByLabelText('Heart rate'), { target: { value: '110' } });
    fireEvent.click(nextButton);
    fireEvent.click(screen.getByRole('button', { name: 'Chest pain' }));
    fireEvent.click(screen.getByRole('button', { name: 'Diabetes' }));
    fireEvent.click(nextButton);

    expect(screen.getAllByText('harsh').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Female/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Ambulance/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('pain').length).toBeGreaterThan(0);
    expect(screen.getAllByText('brief').length).toBeGreaterThan(0);
    expect(screen.getByText('Duration: 1')).toBeInTheDocument();
    expect(screen.getAllByText(/110 bpm/).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Chest pain').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Diabetes').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ready for prediction/i).length).toBeGreaterThan(0);
    expect(createPrediction).not.toHaveBeenCalled();

    const form = screen.getByRole('button', { name: /run esi decision support/i }).closest('form');
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);
    expect(createPrediction).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /run esi decision support/i }));

    await waitFor(() => {
      expect(createPrediction).toHaveBeenCalledWith(
        expect.objectContaining({
          patient_age: 32,
          sex: 'female',
          chief_complaint: 'pain',
          symptom_duration: '1',
          heart_rate: 110,
          additional_context: 'brief'
        })
      );
    });
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/assessments/AS-100'));
  });

  it('submits reviewed NLP audit metadata without the raw clinical note', async () => {
    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'Alex Morgan' } });
    fireEvent.click(screen.getByRole('button', { name: /next/i }));

    const rawClinicalNote =
      '62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2.';
    fireEvent.change(screen.getByLabelText(/clinical note \/ transcript/i), {
      target: { value: rawClinicalNote }
    });
    fireEvent.click(screen.getByRole('button', { name: /extract intake fields/i }));

    await screen.findByText(/clinical intake nlp safety layer/i);
    fireEvent.change(screen.getByLabelText(/duration/i), { target: { value: '2 hours' } });
    fireEvent.click(
      screen.getByRole('checkbox', {
        name: /i reviewed the extracted fields before prediction/i
      })
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(screen.getByRole('button', { name: /run esi decision support/i }));

    await waitFor(() => expect(createPrediction).toHaveBeenCalledTimes(1));
    const submittedPayload = createPrediction.mock.calls[0][0];
    expect(submittedPayload.nlp_extraction_audit).toEqual({
      reviewed: true,
      source: 'clinical_intake_nlp',
      extracted_fields: {
        age: 62,
        gender: 'Male',
        chief_complaint: 'chest pain',
        symptoms: ['chest pain', 'shortness of breath'],
        vitals: {
          hr: 118,
          sbp: 92,
          dbp: 60,
          rr: null,
          o2: 91,
          temp: 38.2
        }
      },
      safety_cues: [
        'chest pain',
        'shortness of breath',
        'low oxygen',
        'low blood pressure',
        'tachycardia'
      ],
      missing_fields: ['respiratory rate'],
      evidence: [
        { field: 'age', value: 62, text: '62-year-old' },
        { field: 'triage_vital_hr', value: 118, text: 'HR 118' },
        { field: 'triage_vital_sbp', value: 92, text: 'BP 92/60' },
        { field: 'triage_vital_o2', value: 91, text: 'O2 91%' }
      ],
      disclaimer: 'Decision support only. Extracted fields require clinician review before prediction.'
    });
    expect(submittedPayload.nlp_extraction_audit).not.toHaveProperty('clinical_note');
    expect(submittedPayload.nlp_extraction_audit).not.toHaveProperty('note_text');
    expect(JSON.stringify(submittedPayload.nlp_extraction_audit)).not.toContain(rawClinicalNote);
  });

  it('prevents duplicate decision-support runs while submission is pending', async () => {
    let resolvePrediction: (value: { assessment_id: string; final_esi: number }) => void = () => undefined;
    createPrediction.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePrediction = resolve;
      })
    );

    render(
      <MemoryRouter>
        <NewAssessmentPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/patient name/i), { target: { value: 'Alex Morgan' } });

    const nextButton = screen.getByRole('button', { name: /next/i });
    fireEvent.click(nextButton);
    fireEvent.change(screen.getByLabelText(/chief complaint/i), { target: { value: 'Chest pain' } });
    fireEvent.change(screen.getByLabelText(/symptom narrative/i), { target: { value: 'Sharp pain' } });
    fireEvent.change(screen.getByLabelText(/duration/i), { target: { value: '2 hours' } });
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    const runButton = screen.getByRole('button', { name: /run esi decision support/i });
    fireEvent.click(runButton);
    fireEvent.click(runButton);

    expect(createPrediction).toHaveBeenCalledTimes(1);

    resolvePrediction({ assessment_id: 'AS-200', final_esi: 3 });
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/assessments/AS-200'));
  });
});
