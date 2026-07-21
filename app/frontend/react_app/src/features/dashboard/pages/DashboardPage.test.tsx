import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardPage } from './DashboardPage';

const { getDashboardSummary } = vi.hoisted(() => ({
  getDashboardSummary: vi.fn()
}));

vi.mock('@/api/dashboard', () => ({ getDashboardSummary }));

describe('DashboardPage', () => {
  beforeEach(() => {
    getDashboardSummary.mockReset();
  });

  it('shows an offline state without presenting failed data as an empty dashboard', async () => {
    getDashboardSummary.mockRejectedValue(new Error('GET /dashboard/summary failed with stack details'));

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Dashboard data could not be loaded right now. Please retry.')).toBeInTheDocument();
    expect(screen.getByText('Recent assessments are temporarily unavailable.')).toBeInTheDocument();
    expect(screen.getByText('ESI distribution is temporarily unavailable.')).toBeInTheDocument();
    expect(screen.getByText('Operational signals are temporarily unavailable.')).toBeInTheDocument();
    expect(screen.queryByText(/No assessments yet/)).not.toBeInTheDocument();
    expect(screen.queryByText(/stack details/)).not.toBeInTheDocument();
  });
});
