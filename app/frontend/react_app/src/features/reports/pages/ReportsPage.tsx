import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, FileText, Plus, Search } from 'lucide-react';
import { useAssessmentsStore } from '@/context/AssessmentsContext';
import { useToast } from '@/context/ToastContext';
import type { AssessmentRecord, ReviewStatus } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EsiBadge } from '@/components/clinical/EsiBadge';
import { ReviewStatusBadge } from '@/components/clinical/ReviewStatusBadge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDateTime } from '@/lib/formatters';
import { generateAssessmentPdf } from '@/lib/reportPdf';

const statusFilters: Array<{ value: ReviewStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'overridden', label: 'Overridden' }
];

function displayedFinalEsi(record: AssessmentRecord) {
  return record.review.status === 'overridden' && record.review.finalDecision !== record.prediction.finalEsi
    ? record.review.finalDecision
    : record.prediction.finalEsi;
}

export function ReportsPage() {
  const { records, isLoading } = useAssessmentsStore();
  const { showToast } = useToast();
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | 'all'>('all');

  const filterCounts = useMemo(
    () => ({
      all: records.length,
      pending: records.filter((record) => record.review.status === 'pending').length,
      accepted: records.filter((record) => record.review.status === 'accepted').length,
      overridden: records.filter((record) => record.review.status === 'overridden').length
    }),
    [records]
  );

  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    return records
      .filter((record) => statusFilter === 'all' || record.review.status === statusFilter)
      .filter((record) => {
        if (!normalized) return true;
        return [
          record.id,
          record.intake.patient.name,
          record.intake.patient.mrn,
          record.intake.chiefComplaint,
          `final esi ${displayedFinalEsi(record)}`,
          `esi ${displayedFinalEsi(record)}`,
          record.review.status
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      });
  }, [query, records, statusFilter]);

  const download = async (record: AssessmentRecord) => {
    await generateAssessmentPdf(record);
    showToast({ tone: 'info', title: 'PDF generated', description: `${record.id}_triageai_report.pdf downloaded.` });
  };

  return (
    <div>
      <PageHeader
        eyebrow="Report center"
        title="Clinical PDF Reports"
        description="Download decision-support summaries with patient context, final routing decision, model output, safety rules, latency, confidence, clinician review, and audit metadata."
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
          <CardBody className="overflow-x-auto p-0">
            {isLoading ? (
              <SkeletonTableRows rows={6} cols={6} />
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
              <table className="w-full min-w-[800px] text-left text-sm">
                <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Report / Assessment</th>
                    <th className="px-5 py-3">Patient</th>
                    <th className="px-5 py-3">Final ESI</th>
                    <th className="px-5 py-3">Review Status</th>
                    <th className="px-5 py-3">Created</th>
                    <th className="px-5 py-3 text-right">Download</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((record) => (
                    <tr key={record.id} className="align-top transition hover:bg-slate-50/80">
                      <td className="px-5 py-4">
                        <p className="font-data font-bold text-clinical-blue">{record.id}</p>
                        <p className="font-data text-xs text-slate-500">{record.prediction.requestId}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="font-bold leading-5 text-slate-950">{record.intake.patient.name}</p>
                        <p className="font-data text-xs text-slate-500">{record.intake.patient.mrn}</p>
                      </td>
                      <td className="px-5 py-4">
                        <EsiBadge level={displayedFinalEsi(record)} />
                      </td>
                      <td className="px-5 py-4">
                        <ReviewStatusBadge status={record.review.status} />
                      </td>
                      <td className="px-5 py-4 text-slate-500">{formatDateTime(record.prediction.createdAt)}</td>
                      <td className="px-5 py-4 text-right">
                        <Button variant="secondary" onClick={() => download(record)}>
                          <Download size={15} /> Download PDF
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
