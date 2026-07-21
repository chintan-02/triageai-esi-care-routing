import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ReportsPage } from './ReportsPage';

const { listAssessments, getAssessmentAudit, downloadReportPdf } = vi.hoisted(() => ({
  listAssessments: vi.fn(),
  getAssessmentAudit: vi.fn(),
  downloadReportPdf: vi.fn()
}));

vi.mock('@/api/assessments', () => ({
  listAssessments,
  getAssessmentAudit
}));

vi.mock('@/api/reports', () => ({
  downloadReportPdf
}));

vi.mock('@/context/ToastContext', () => ({
  useToast: () => ({ showToast: vi.fn() })
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <ReportsPage />
    </MemoryRouter>
  );
}

describe('ReportsPage', () => {
  beforeEach(() => {
    listAssessments.mockReset();
    getAssessmentAudit.mockReset();
    downloadReportPdf.mockReset();
    listAssessments.mockResolvedValue([
      {
        assessment_id: 'AS-100',
        patient_name: 'Alex Morgan',
        mrn: 'MRN-100',
        chief_complaint: 'Chest pain',
        model_predicted_esi: 3,
        final_esi: 2,
        safety_escalated: true,
        review_status_normalized: 'accepted',
        created_at: '2026-07-14T15:00:00Z',
        updated_at: '2026-07-14T15:05:00Z',
        report_ids: ['REP-100']
      },
      {
        assessment_id: 'AS-200',
        patient_name: 'No Report Patient',
        mrn: 'MRN-200',
        final_esi: 4,
        safety_escalated: false,
        review_status_normalized: 'pending',
        report_ids: []
      }
    ]);
    getAssessmentAudit.mockResolvedValue({
      assessment_id: 'AS-100',
      events: [
        {
          audit_id: 'AUD-REPORT-1',
          action: 'report_generated',
          actor_id: 'backend_api',
          created_at: '2026-07-14T15:06:00Z',
          details: {
            report_id: 'REP-100',
            report_status: 'generated'
          }
        }
      ]
    });
  });

  it('renders a real report center with report, assessment, routing, review, and visible actions', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: 'PDF decision-support summaries' })).toBeInTheDocument();
    expect(screen.getByText(/Generated reports summarize structured intake/)).toBeInTheDocument();
    expect(screen.getByText('Total reports').parentElement).toHaveTextContent('1');
    expect(screen.getByText('Generated reports', { selector: 'p' }).parentElement).toHaveTextContent('1');
    expect(screen.getByText('Clinician review completed').parentElement).toHaveTextContent('1');
    expect(screen.getByText('Most recent report')).toBeInTheDocument();

    const reportCard = screen.getByText('REP-100').closest('article');
    expect(reportCard).not.toBeNull();
    expect(within(reportCard as HTMLElement).getByText('AS-100')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByText('Alex Morgan')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByText('MRN-100 • Chest pain')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByText('ESI 2')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByText('Accepted')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByText('generated')).toBeInTheDocument();
    expect(within(reportCard as HTMLElement).getByRole('button', { name: 'Download PDF' })).toBeEnabled();
    expect(within(reportCard as HTMLElement).getByRole('link', { name: 'View Assessment' })).toHaveAttribute('href', '/assessments/AS-100');
    expect(screen.queryByText('No Report Patient')).not.toBeInTheDocument();
  });

  it('shows the report-specific empty state and assessment path', async () => {
    listAssessments.mockResolvedValue([
      {
        assessment_id: 'AS-200',
        safety_escalated: false,
        report_ids: []
      }
    ]);

    renderPage();

    expect(await screen.findByText('No reports generated yet.')).toBeInTheDocument();
    expect(screen.getByText('Reports are created from assessment detail pages after decision-support review.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View assessments' })).toHaveAttribute('href', '/assessments');
    expect(getAssessmentAudit).not.toHaveBeenCalled();
  });

  it('shows a calm retry state without raw endpoint details', async () => {
    listAssessments.mockRejectedValue(new Error('GET /assessments failed with stack details'));

    renderPage();

    expect(await screen.findByText('Reports could not be loaded right now. Please retry.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
    expect(screen.getByText('The report list is temporarily unavailable.')).toBeInTheDocument();
    expect(screen.queryByText(/stack details/)).not.toBeInTheDocument();
  });
});
