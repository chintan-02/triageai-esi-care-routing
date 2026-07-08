import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NewAssessmentPage } from './NewAssessmentPage';

const { createPrediction } = vi.hoisted(() => ({
  createPrediction: vi.fn()
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

vi.mock('@/context/ToastContext', () => ({
  useToast: () => ({ showToast })
}));

describe('NewAssessmentPage', () => {
  beforeEach(() => {
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
