import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, Clock3, Download, FileText, Search } from 'lucide-react';
import { getAssessmentAudit, listAssessments } from '@/api/assessments';
import { downloadReportPdf } from '@/api/reports';
import { useToast } from '@/context/ToastContext';
import type { AssessmentAuditEvent, AssessmentListItem } from '@/types/api';
import type { EsiLevel, ReviewStatus } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { EsiBadge } from '@/components/clinical/EsiBadge';
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
  reportId: string;
  assessmentId: string;
  patientName: string;
  mrn: string;
  chiefComplaint: string;
  finalEsi: EsiLevel | null;
  reviewStatus: ReviewStatus;
  generatedAt: string | null;
  reportStatus: string;
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

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function auditPayload(event: AssessmentAuditEvent): Record<string, unknown> {
  if (!isPlainRecord(event.details)) return {};
  const payload = event.details.payload;
  return isPlainRecord(payload) ? { ...event.details, ...payload } : event.details;
}

function reportEventForId(events: AssessmentAuditEvent[], reportId: string): AssessmentAuditEvent | undefined {
  return [...events].reverse().find((event) => {
    const action = event.action.toLowerCase();
    return (action.includes('report') || action.includes('pdf')) && auditPayload(event).report_id === reportId;
  });
}

function mapReportRows(item: AssessmentListItem, events: AssessmentAuditEvent[]): ReportRow[] {
  if (!Array.isArray(item.report_ids)) return [];
  return item.report_ids.map((reportId) => {
    const event = reportEventForId(events, reportId);
    const payload = event ? auditPayload(event) : {};
    const reportStatus = typeof payload.report_status === 'string' && payload.report_status.trim()
      ? payload.report_status.replace(/_/g, ' ')
      : event ? 'generated' : 'status unavailable';
    return {
      reportId,
      assessmentId: item.assessment_id,
      patientName: textOrFallback(item.patient_name, '—'),
      mrn: textOrFallback(item.mrn, '—'),
      chiefComplaint: textOrFallback(item.chief_complaint, '—'),
      finalEsi: isEsiLevel(item.final_esi) ? item.final_esi : null,
      reviewStatus: normalizeReviewStatus(item),
      generatedAt: event?.timestamp ?? event?.created_at ?? null,
      reportStatus,
    };
  });
}

function reportStatusTone(status: string): string {
  return status.toLowerCase() === 'generated'
    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
    : 'border-slate-200 bg-slate-50 text-slate-700';
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
  const [records, setRecords] = useState<ReportRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const loaded = await listAssessments();
      const assessmentsWithReports = loaded.filter(
        (item) => Array.isArray(item.report_ids) && item.report_ids.length > 0,
      );
      const reportGroups = await Promise.all(
        assessmentsWithReports.map(async (item) => {
          try {
            const audit = await getAssessmentAudit(item.assessment_id);
            return mapReportRows(item, audit.events);
          } catch {
            return mapReportRows(item, []);
          }
        }),
      );
      setRecords(
        reportGroups
          .flat()
          .sort((a, b) => +new Date(b.generatedAt ?? 0) - +new Date(a.generatedAt ?? 0)),
      );
    } catch {
      setRecords([]);
      setLoadError('Reports could not be loaded right now. Please retry.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

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
          record.reportId,
          record.assessmentId,
          record.patientName,
          record.mrn,
          record.chiefComplaint,
          `final esi ${record.finalEsi ?? 'n/a'}`,
          `esi ${record.finalEsi ?? 'n/a'}`,
          record.reviewStatus,
          record.reportStatus,
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      });
  }, [query, records, statusFilter]);

  const reportSummary = useMemo(() => {
    const generated = records.filter((record) => record.reportStatus.toLowerCase() === 'generated');
    const reviewed = records.filter(
      (record) => record.reviewStatus === 'accepted' || record.reviewStatus === 'overridden',
    );
    const mostRecent = records
      .map((record) => record.generatedAt)
      .filter((value): value is string => Boolean(value))
      .sort((a, b) => +new Date(b) - +new Date(a))[0] ?? null;
    return { total: records.length, generated: generated.length, reviewed: reviewed.length, mostRecent };
  }, [records]);

  const download = async (record: ReportRow) => {
    setDownloadingId(record.reportId);
    try {
      const blob = await downloadReportPdf(record.reportId);
      saveBlob(blob, `triageai_report_${record.reportId}.pdf`);
      showToast({ tone: 'info', title: 'PDF downloaded', description: `Report ${record.reportId} downloaded.` });
    } catch {
      showToast({
        tone: 'error',
        title: 'PDF unavailable',
        description: 'The report PDF could not be downloaded. Please try again.'
      });
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Reports"
        title="PDF decision-support summaries"
        description="Generated reports summarize structured intake, model output, safety-rule escalation, clinician review, NLP evidence, and audit context. Decision support only."
      />

      {!isLoading && !loadError ? (
        <div className={`mb-6 grid gap-4 sm:grid-cols-2 ${reportSummary.mostRecent ? 'xl:grid-cols-4' : 'xl:grid-cols-3'}`}>
          <Card><CardBody className="flex items-center gap-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><FileText size={20} /></div><div><p className="text-xs font-black uppercase tracking-wide text-slate-500">Total reports</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{reportSummary.total}</p></div></CardBody></Card>
          <Card><CardBody className="flex items-center gap-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700"><CheckCircle2 size={20} /></div><div><p className="text-xs font-black uppercase tracking-wide text-slate-500">Generated reports</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{reportSummary.generated}</p></div></CardBody></Card>
          <Card><CardBody className="flex items-center gap-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-violet-50 text-violet-700"><CheckCircle2 size={20} /></div><div><p className="text-xs font-black uppercase tracking-wide text-slate-500">Clinician review completed</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{reportSummary.reviewed}</p></div></CardBody></Card>
          {reportSummary.mostRecent ? (
            <Card><CardBody className="flex items-center gap-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-50 text-amber-700"><Clock3 size={20} /></div><div><p className="text-xs font-black uppercase tracking-wide text-slate-500">Most recent report</p><p className="mt-1 text-sm font-black text-slate-950">{formatDateTime(reportSummary.mostRecent)}</p></div></CardBody></Card>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <Card>
          <CardHeader
            title="Generated reports"
            description="Review and download audit-ready PDF summaries linked to stored assessments."
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
                type="button"
                aria-pressed={statusFilter === filter.value}
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
          <CardBody className="p-0">
            {isLoading ? (
              <div className="p-5"><SkeletonTableRows rows={5} cols={4} /></div>
            ) : loadError ? (
              <div className="p-6 text-center text-sm font-semibold text-slate-500">The report list is temporarily unavailable.</div>
            ) : records.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  title="No reports generated yet."
                  description="Reports are created from assessment detail pages after decision-support review."
                  action={
                    <Link to="/assessments">
                      <Button variant="secondary">
                        <FileText size={17} /> View assessments
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
              <div className="space-y-3 p-5">
                {filtered.map((record) => (
                  <article key={record.reportId} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-card sm:p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="flex min-w-0 gap-3.5">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><FileText size={20} /></div>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-data font-black text-slate-950 [overflow-wrap:anywhere]">{record.reportId}</h3>
                            <Badge className={reportStatusTone(record.reportStatus)}>{record.reportStatus}</Badge>
                          </div>
                          <p className="mt-1 text-sm font-bold text-slate-800">{record.patientName}</p>
                          <p className="mt-0.5 text-xs font-semibold text-slate-500">{record.mrn} • {record.chiefComplaint}</p>
                        </div>
                      </div>
                      <div className="flex shrink-0 flex-wrap gap-2">
                        <Link to={`/assessments/${encodeURIComponent(record.assessmentId)}`}>
                          <Button variant="secondary">View Assessment</Button>
                        </Link>
                        <Button onClick={() => void download(record)} disabled={downloadingId === record.reportId}>
                          <Download size={15} /> {downloadingId === record.reportId ? 'Downloading...' : 'Download PDF'}
                        </Button>
                      </div>
                    </div>

                    <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="rounded-2xl bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wide text-slate-400">Assessment ID</p><p className="font-data mt-1 text-sm font-bold text-slate-800 [overflow-wrap:anywhere]">{record.assessmentId}</p></div>
                      <div className="rounded-2xl bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wide text-slate-400">Final routing</p><div className="mt-1.5">{record.finalEsi ? <EsiBadge level={record.finalEsi} /> : <span className="text-sm font-semibold text-slate-500">Not captured</span>}</div></div>
                      <div className="rounded-2xl bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wide text-slate-400">Clinician review</p><div className="mt-1.5"><ReviewStatusBadge status={record.reviewStatus} /></div></div>
                      <div className="rounded-2xl bg-slate-50 p-3"><p className="text-[10px] font-black uppercase tracking-wide text-slate-400">Generated</p><p className="mt-1 text-sm font-bold text-slate-800">{record.generatedAt ? formatDateTime(record.generatedAt) : 'Time unavailable'}</p></div>
                    </div>
                  </article>
                ))}
              </div>
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
              'Clinical NLP review evidence',
              'Audit metadata',
              'Decision-support disclaimer'
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
