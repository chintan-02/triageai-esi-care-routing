import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NewAssessmentPage } from './NewAssessmentPage';

const createAssessment = vi.fn();
const showToast = vi.fn();
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate
  };
});

vi.mock('@/context/AssessmentsContext', () => ({
  useAssessmentsStore: () => ({ createAssessment })
}));

vi.mock('@/context/ToastContext', () => ({
  useToast: () => ({ showToast })
}));

describe('NewAssessmentPage', () => {
  beforeEach(() => {
    createAssessment.mockReset();
    showToast.mockReset();
    mockNavigate.mockReset();
    createAssessment.mockResolvedValue({
      id: 'AS-100',
      prediction: { finalEsi: 3, latencyMs: 42 }
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
    expect(createAssessment).not.toHaveBeenCalled();
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
    expect(createAssessment).not.toHaveBeenCalled();

    const form = screen.getByRole('button', { name: /run esi decision support/i }).closest('form');
    expect(form).not.toBeNull();
    fireEvent.submit(form as HTMLFormElement);
    expect(createAssessment).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /run esi decision support/i }));

    await waitFor(() => {
      expect(createAssessment).toHaveBeenCalledWith(
        expect.objectContaining({
          patient: expect.objectContaining({ name: 'harsh' }),
          chiefComplaint: 'pain',
          symptomText: 'brief',
          duration: '1',
          vitals: expect.objectContaining({ heartRate: 110 }),
          riskFlags: expect.arrayContaining(['Chest pain']),
          comorbidities: expect.arrayContaining(['Diabetes'])
        })
      );
    });
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/assessments/AS-100'));
  });

  it('prevents duplicate decision-support runs while submission is pending', async () => {
    let resolveAssessment: (value: { id: string; prediction: { finalEsi: number; latencyMs: number } }) => void = () => undefined;
    createAssessment.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveAssessment = resolve;
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

    expect(createAssessment).toHaveBeenCalledTimes(1);

    resolveAssessment({ id: 'AS-200', prediction: { finalEsi: 3, latencyMs: 55 } });
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/assessments/AS-200'));
  });
});
