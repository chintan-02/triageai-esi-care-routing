import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowUpRight, Plus, Search } from 'lucide-react';
import { useAssessmentsStore } from '@/context/AssessmentsContext';
import { useAuth } from '@/context/AuthContext';
import { hasPermission } from '@/lib/permissions';
import type { ReviewStatus } from '@/types/clinical';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EsiBadge } from '@/components/clinical/EsiBadge';
import { ReviewStatusBadge } from '@/components/clinical/ReviewStatusBadge';
import { LatencyBadge } from '@/components/clinical/LatencyBadge';
import { SkeletonTableRows } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatDateTime, formatPercent } from '@/lib/formatters';

const statusFilters: Array<{ value: ReviewStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'overridden', label: 'Overridden' }
];

export function AssessmentsPage() {
  const { records, isLoading, error, refresh } = useAssessmentsStore();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('search') ?? '');
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | 'all'>('all');
  const canCreateAssessment = hasPermission(user?.role, 'assessment:create');

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
          record.prediction.modelVersion,
          `pred esi ${record.prediction.predictedEsi}`,
          `predicted esi ${record.prediction.predictedEsi}`,
          `final esi ${record.prediction.finalEsi}`,
          `esi ${record.prediction.finalEsi}`,
          record.review.status
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      });
  }, [query, records, statusFilter]);

  return (
    <div>
      <PageHeader
        eyebrow="Assessment Queue"
        title="Patient Assessments"
        description="Review model-assisted ESI outputs, final routing decisions, confidence, safety escalation, and clinician status."
        actions={
          canCreateAssessment ? (
            <Link to="/new-assessment">
              <Button>
                <Plus size={17} /> New Assessment
              </Button>
            </Link>
          ) : null
        }
      />

      <Card>
        <CardHeader
          title="Assessment registry"
          description="Clinical worklist for assessment review and routing status."
          action={
            <div className="flex min-h-[42px] items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 focus-within:ring-2 focus-within:ring-clinical-blue/20">
              <Search size={17} />
              <input
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  const next = new URLSearchParams(searchParams);
                  if (event.target.value.trim()) next.set('search', event.target.value);
                  else next.delete('search');
                  setSearchParams(next, { replace: true });
                }}
                placeholder="Search assessments..."
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
        {error ? (
          <div className="border-b border-red-100 bg-red-50 px-5 py-4 text-sm text-red-800">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span><strong>Could not load assessments.</strong> {error}</span>
              <Button variant="danger" onClick={() => void refresh()} className="px-3 py-2">Retry</Button>
            </div>
          </div>
        ) : null}
        <CardBody className="overflow-x-auto p-0">
          {isLoading ? (
            <SkeletonTableRows rows={6} cols={8} />
          ) : filtered.length === 0 ? (
            <div className="p-6">
              <EmptyState
                title={query.trim() ? 'No matching assessments found' : 'No assessments match this filter'}
                description={query.trim() ? 'Try a different assessment ID, patient, MRN, complaint, ESI, or review status.' : 'Try another review status or return to the full assessment registry.'}
              />
            </div>
          ) : (
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3">Assessment</th>
                  <th className="px-5 py-3">Patient</th>
                  <th className="px-5 py-3">Complaint</th>
                  <th className="px-5 py-3">Model</th>
                  <th className="px-5 py-3">Final</th>
                  <th className="px-5 py-3">Latency</th>
                  <th className="px-5 py-3">Review</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((record) => (
                  <tr key={record.id} className="align-top transition hover:bg-slate-50/80">
                    <td className="px-5 py-4">
                      <Link to={`/assessments/${record.id}`} className="font-data font-bold text-clinical-blue hover:text-blue-800">
                        {record.id}
                      </Link>
                      <p className="text-xs text-slate-500">{formatDateTime(record.prediction.createdAt)}</p>
                    </td>
                    <td className="px-5 py-4">
                      <p className="font-bold leading-5 text-slate-950">{record.intake.patient.name}</p>
                      <p className="font-data text-xs text-slate-500">
                        {record.intake.patient.age} • {record.intake.patient.sex || 'Unknown'} • {record.intake.patient.mrn}
                      </p>
                    </td>
                    <td className="px-5 py-4">
                      <p className="max-w-[260px] overflow-hidden text-ellipsis leading-5 text-slate-600 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">
                        {record.intake.chiefComplaint}
                      </p>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-col items-start gap-1">
                        <EsiBadge level={record.prediction.predictedEsi} prefix="Pred" />
                      </div>
                      <p className="mt-1 text-xs font-semibold text-slate-500">{formatPercent(record.prediction.confidence)}</p>
                    </td>
                    <td className="px-5 py-4">
                      <EsiBadge level={record.prediction.finalEsi} />
                    </td>
                    <td className="px-5 py-4">
                      <LatencyBadge ms={record.prediction.latencyMs} size="sm" />
                    </td>
                    <td className="px-5 py-4">
                      <ReviewStatusBadge status={record.review.status} />
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link to={`/assessments/${record.id}`}>
                        <Button variant="secondary" className="px-3 py-2">
                          Open <ArrowUpRight size={15} />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
