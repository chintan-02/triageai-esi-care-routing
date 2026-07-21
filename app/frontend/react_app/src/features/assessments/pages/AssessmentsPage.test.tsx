import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AssessmentsPage } from './AssessmentsPage';

const { listAssessments } = vi.hoisted(() => ({ listAssessments: vi.fn() }));

vi.mock('@/api/assessments', () => ({ listAssessments }));
vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'Nurse' } })
}));

describe('AssessmentsPage', () => {
  beforeEach(() => {
    listAssessments.mockReset();
  });

  it('distinguishes an unavailable registry from a valid empty result', async () => {
    listAssessments.mockRejectedValue(new Error('GET /assessments failed with stack details'));

    render(
      <MemoryRouter>
        <AssessmentsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Assessments could not be loaded right now. Please retry.')).toBeInTheDocument();
    expect(screen.getByText('The assessment registry is temporarily unavailable.')).toBeInTheDocument();
    expect(screen.queryByText('No assessments match this filter')).not.toBeInTheDocument();
    expect(screen.queryByText(/stack details/)).not.toBeInTheDocument();
  });
});
