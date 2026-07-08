import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, FileText, Plus, Search } from 'lucide-react';
import { listAssessments } from '@/api/assessments';
import { downloadAssessmentPdf } from '@/api/reports';
import { useToast } from '@/context/ToastContext';
import type { AssessmentListItem } from '@/types/api';
import type { EsiLevel, ReviewStatus } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EsiBadge } from '@/components/clinical/EsiBadge';
import { LatencyBadge } from '@/components/clinical/LatencyBadge';
import { ReviewStatusBadge } from '@/components/clinical/ReviewStatusBadge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDateTime } from '@/lib/formatters';

const statusFilters: Array<{ value: ReviewStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'overridden', label: 'Overridden' }
];

type ReportRow = {
  id: string;
  patientName: string;
  mrn: string;
  chiefComplaint: string;
  finalEsi: EsiLevel | null;
  predictedEsi: EsiLevel | null;
  latencyMs: number | null;
  reviewStatus: ReviewStatus;
  createdAt: string | null;
  hasBackendReport: boolean;
};

function textOrFallback(value: string | null | undefined, fallback: string): string {
  return value?.trim() || fallback;
}

function isEsiLevel(value: unknown): value is EsiLevel {
  return typeof value === 'number' && [1, 2, 3, 4, 5].includes(value);
}

function normalizeReviewStatus(item: AssessmentListItem): ReviewStatus {
  const rawStatus = item.review_status_normalized ?? item.review_status ?? item.status;
  if (rawStatus === 'accepted' || rawStatus === 'overridden') return rawStatus;
  return 'pending';
}

function mapReportRow(item: AssessmentListItem): ReportRow {
  return {
    id: item.assessment_id,
    patientName: textOrFallback(item.patient_name, '—'),
    mrn: textOrFallback(item.mrn, '—'),
    chiefComplaint: textOrFallback(item.chief_complaint, '—'),
    finalEsi: isEsiLevel(item.final_esi) ? item.final_esi : null,
    predictedEsi: isEsiLevel(item.model_predicted_esi) ? item.model_predicted_esi : null,
    latencyMs: typeof item.latency_ms === 'number' ? item.latency_ms : null,
    reviewStatus: normalizeReviewStatus(item),
    createdAt: item.created_at ?? item.updated_at ?? null,
    hasBackendReport: Array.isArray(item.report_ids) && item.report_ids.length > 0,
  };
}

function shortAssessmentId(id: string): string {
  return id.split('-')[0] || id.slice(0, 8);
}

function EsiCell({ level, prefix }: { level: EsiLevel | null; prefix?: string }) {
  if (!level) return <span className="text-xs font-semibold text-slate-500">—</span>;
  return <EsiBadge level={level} prefix={prefix} />;
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function ReportsPage() {
  const { showToast } = useToast();
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | 'all'>('all');
  const [assessments, setAssessments] = useState<AssessmentListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const loaded = await listAssessments();
      setAssessments(loaded);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Backend request failed.';
      setLoadError(`Unable to load real backend assessments from GET /assessments. ${message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const records = useMemo(() => assessments.map(mapReportRow), [assessments]);

  const filterCounts = useMemo(
    () => ({
      all: records.length,
      pending: records.filter((record) => record.reviewStatus === 'pending').length,
      accepted: records.filter((record) => record.reviewStatus === 'accepted').length,
      overridden: records.filter((record) => record.reviewStatus === 'overridden').length
    }),
    [records]
  );

  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    return records
      .filter((record) => statusFilter === 'all' || record.reviewStatus === statusFilter)
      .filter((record) => {
        if (!normalized) return true;
        return [
          record.id,
          record.patientName,
          record.mrn,
          record.chiefComplaint,
          `final esi ${record.finalEsi ?? 'n/a'}`,
          `model esi ${record.predictedEsi ?? 'n/a'}`,
          `predicted esi ${record.predictedEsi ?? 'n/a'}`,
          `latency ${record.latencyMs ?? 'not captured'}`,
          `esi ${record.finalEsi ?? record.predictedEsi ?? 'n/a'}`,
          record.reviewStatus,
          record.hasBackendReport ? 'available' : 'on demand'
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      });
  }, [query, records, statusFilter]);

  const download = async (record: ReportRow) => {
    setDownloadingId(record.id);
    try {
      const blob = await downloadAssessmentPdf(record.id);
      saveBlob(blob, `${record.id}_triageai_report.pdf`);
      showToast({ tone: 'info', title: 'PDF generated', description: `${record.id}_triageai_report.pdf downloaded.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Backend PDF generation failed.';
      showToast({
        tone: 'error',
        title: 'PDF unavailable',
        description: `GET /assessments/${record.id}/report/pdf failed. ${message}`
      });
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Report center"
        title="Clinical PDF Reports"
        description="Download decision-support summaries for ESI care routing with patient context, model output, safety rules, confidence, clinician review, audit metadata, and a clear note that this is not diagnosis and does not replace clinician judgment."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <Card>
          <CardHeader
            title="Available reports"
            description="Audit-ready PDF summaries for stored assessments."
            action={
              <div className="flex min-h-[42px] items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 focus-within:ring-2 focus-within:ring-clinical-blue/20">
                <Search size={17} />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search reports..."
                  className="w-56 bg-transparent outline-none"
                />
              </div>
            }
          />
          <div className="flex flex-wrap gap-2 border-b border-slate-100 bg-white px-5 py-4">
            {statusFilters.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setStatusFilter(filter.value)}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold transition ${
                  statusFilter === filter.value ? 'border-clinical-navy bg-clinical-navy text-white shadow-sm' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span>{filter.label}</span>
                <span className={`font-data rounded-full px-1.5 py-0.5 text-[10px] ${statusFilter === filter.value ? 'bg-white/15 text-white' : 'bg-slate-100 text-slate-500'}`}>
                  {filterCounts[filter.value]}
                </span>
              </button>
            ))}
          </div>
          {loadError ? (
            <div className="border-b border-red-100 bg-red-50 px-5 py-4 text-sm text-red-800">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <span><strong>Could not load reports.</strong> {loadError}</span>
                <Button variant="danger" onClick={() => void refresh()} className="px-3 py-2">Retry</Button>
              </div>
            </div>
          ) : null}
          <CardBody className="overflow-x-auto p-0">
            {isLoading ? (
              <SkeletonTableRows rows={6} cols={8} />
            ) : records.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  title="No reports available yet"
                  description="Complete an assessment to generate a PDF summary."
                  action={
                    <Link to="/new-assessment">
                      <Button>
                        <Plus size={17} /> Start new intake
                      </Button>
                    </Link>
                  }
                />
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  title="No matching reports found"
                  description="Try a different assessment ID, patient, MRN, final ESI, review status, or complaint."
                />
              </div>
            ) : (
              <table className="w-full min-w-[960px] text-left text-sm">
                <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Report / Assessment</th>
                    <th className="px-5 py-3">Patient</th>
                    <th className="px-5 py-3">Model ESI</th>
                    <th className="px-5 py-3">Final ESI</th>
                    <th className="px-5 py-3">Latency</th>
                    <th className="px-5 py-3">Review Status</th>
                    <th className="px-5 py-3">Created</th>
                    <th className="px-5 py-3 text-right">Download</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((record) => (
                    <tr key={record.id} className="align-top transition hover:bg-slate-50/80">
                      <td className="px-5 py-4">
                        <p className="font-data font-bold text-clinical-blue" title={record.id}>{shortAssessmentId(record.id)}</p>
                        <p className="font-data text-xs text-slate-500">{record.hasBackendReport ? 'Backend PDF available' : 'Backend PDF on demand'}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="font-bold leading-5 text-slate-950">{record.patientName}</p>
                        <p className="font-data text-xs text-slate-500">{record.mrn}</p>
                      </td>
                      <td className="px-5 py-4">
                        <EsiCell level={record.predictedEsi} prefix="Pred" />
                      </td>
                      <td className="px-5 py-4">
                        <EsiCell level={record.finalEsi} />
                      </td>
                      <td className="px-5 py-4">
                        {record.latencyMs === null ? (
                          <span className="text-xs font-semibold text-slate-500">—</span>
                        ) : (
                          <LatencyBadge ms={record.latencyMs} size="sm" />
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <ReviewStatusBadge status={record.reviewStatus} />
                      </td>
                      <td className="px-5 py-4 text-slate-500">{record.createdAt ? formatDateTime(record.createdAt) : '—'}</td>
                      <td className="px-5 py-4 text-right">
                        <Button variant="secondary" onClick={() => void download(record)} disabled={downloadingId === record.id}>
                          <Download size={15} /> {downloadingId === record.id ? 'Generating...' : record.hasBackendReport ? 'Download PDF' : 'Generate PDF'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Decision-support summary includes" description="Core sections included in each audit-ready PDF summary." />
          <CardBody className="space-y-4">
            {[
              'Final routing decision',
              'Model prediction and raw probabilities',
              'Safety-rule escalation',
              'Confidence and latency',
              'Abnormal vitals highlighting',
              'Clinician review status',
              'Audit metadata',
              'Clinical disclaimer'
            ].map((item) => (
              <div key={item} className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-3 text-sm font-semibold text-slate-700">
                <FileText className="mt-0.5 text-clinical-model" size={17} /> {item}
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
