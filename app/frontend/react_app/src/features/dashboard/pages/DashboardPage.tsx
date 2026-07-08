import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowUpRight, Clock, FileText, Plus, ShieldCheck, Timer } from 'lucide-react';
import { useAssessmentsStore } from '@/context/AssessmentsContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { EsiBadge } from '@/components/clinical/EsiBadge';
import { ReviewStatusBadge } from '@/components/clinical/ReviewStatusBadge';
import { LatencyBadge } from '@/components/clinical/LatencyBadge';
import { EsiDistributionDonut } from '@/components/charts/EsiDistributionDonut';
import { OperationalTrendChart } from '@/components/charts/OperationalTrendChart';
import { SkeletonBlock, SkeletonStatRow, SkeletonTableRows } from '@/components/ui/Skeleton';
import { formatDateTime, formatPercent } from '@/lib/formatters';
import type { AssessmentRecord } from '@/types/clinical';

function hasSafetyReview(record: AssessmentRecord) {
  return record.prediction.ruleHits.length > 0 || record.prediction.finalEsi !== record.prediction.predictedEsi;
}

function displayedFinalEsi(record: AssessmentRecord) {
  return record.review.status === 'overridden' && record.review.finalDecision !== record.prediction.finalEsi
    ? record.review.finalDecision
    : record.prediction.finalEsi;
}

export function DashboardPage() {
  const { records, isLoading } = useAssessmentsStore();
  const recent = useMemo(() => [...records].sort((a, b) => +new Date(b.prediction.createdAt) - +new Date(a.prediction.createdAt)).slice(0, 6), [records]);
  const stats = useMemo(() => {
    const totalAssessments = records.length;
    const pendingReviews = records.filter((record) => record.review.status === 'pending').length;
    const safetyEscalations = records.filter(hasSafetyReview).length;
    const avgLatencyMs = Math.round(records.reduce((sum, record) => sum + record.prediction.latencyMs, 0) / Math.max(totalAssessments, 1));
    const esiDistribution = records.reduce<Record<string, number>>((acc, record) => {
      const key = `ESI ${displayedFinalEsi(record)}`;
      acc[key] = (acc[key] ?? 0) + 1;
      return acc;
    }, {});

    return { totalAssessments, pendingReviews, safetyEscalations, avgLatencyMs, esiDistribution };
  }, [records]);

  return (
    <div>
      <PageHeader
        eyebrow="Clinical Command Center"
        title="ESI Intake & Care Routing Overview"
        description="Monitor patient assessments, safety escalations, model confidence, latency, and clinician review status from one operational workspace."
        actions={
          <>
            <Link to="/reports">
              <Button variant="secondary">
                <FileText size={17} /> View Reports
              </Button>
            </Link>
            <Link to="/new-assessment">
              <Button>
                <Plus size={17} /> New Assessment
              </Button>
            </Link>
          </>
        }
      />

      {isLoading ? (
        <SkeletonStatRow />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Assessments" value={stats.totalAssessments} hint="Loaded from current assessment store" icon={<Activity size={22} />} tone="blue" />
          <StatCard label="Pending Reviews" value={stats.pendingReviews} hint="Clinician review still required" icon={<Clock size={22} />} tone="amber" />
          <StatCard label="Safety Escalations" value={stats.safetyEscalations} hint="Rules changed or confirmed acuity" icon={<AlertTriangle size={22} />} tone="red" />
          <StatCard
            label="Avg Latency"
            value={`${stats.avgLatencyMs} ms`}
            hint="Prediction response time"
            icon={<Timer size={22} />}
            tone="model"
          />
        </div>
      )}

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
        <Card>
          <CardHeader title="Recent assessments" description="Latest stored assessments with final routing decision, latency, and clinician review status." />
          <CardBody className="overflow-x-auto p-0">
            {isLoading ? (
              <SkeletonTableRows rows={6} cols={7} />
            ) : recent.length === 0 ? (
              <div className="flex flex-col items-start gap-4 p-6">
                <p className="text-sm text-slate-600">No assessments yet. Start a structured intake to generate a decision-support summary.</p>
                <Link to="/new-assessment">
                  <Button>
                    <Plus size={17} /> Create new assessment
                  </Button>
                </Link>
              </div>
            ) : (
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Patient</th>
                    <th className="px-5 py-3">Complaint</th>
                    <th className="px-5 py-3">Final ESI</th>
                    <th className="px-5 py-3">Latency</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Created</th>
                    <th className="px-5 py-3 text-right">Open</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recent.map((record) => (
                    <tr key={record.id} className="hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <Link to={`/assessments/${record.id}`} className="font-bold text-slate-950 hover:text-clinical-blue">
                          {record.intake.patient.name}
                        </Link>
                        <p className="font-data text-xs text-slate-500">{record.intake.patient.mrn}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="max-w-[240px] overflow-hidden text-ellipsis text-slate-700 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">
                          {record.intake.chiefComplaint}
                        </p>
                        {hasSafetyReview(record) ? <p className="mt-1 text-xs font-bold text-red-700">Safety-rule review</p> : null}
                      </td>
                      <td className="px-5 py-4">
                        <EsiBadge level={displayedFinalEsi(record)} />
                        <p className="mt-1 text-xs font-semibold text-slate-500">{formatPercent(record.prediction.confidence)} confidence</p>
                      </td>
                      <td className="px-5 py-4">
                        <LatencyBadge ms={record.prediction.latencyMs} size="sm" />
                      </td>
                      <td className="px-5 py-4">
                        <ReviewStatusBadge status={record.review.status} />
                      </td>
                      <td className="px-5 py-4 text-slate-500">{formatDateTime(record.prediction.createdAt)}</td>
                      <td className="px-5 py-4 text-right">
                        <Link to={`/assessments/${record.id}`}>
                          <Button variant="ghost" className="px-3 py-2">
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

        <div className="space-y-6">
          <Card>
            <CardHeader title="Final ESI distribution" description="Final routing decisions across stored assessments." />
            <CardBody>
              {isLoading ? <SkeletonBlock className="h-40 w-full" /> : <EsiDistributionDonut distribution={stats.esiDistribution} />}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Operational signals" description="Latency and confidence across recent assessments." />
            <CardBody className="space-y-5">
              {isLoading ? (
                <SkeletonBlock className="h-40 w-full" />
              ) : (
                <>
                  <OperationalTrendChart records={records} />
                  <div className="rounded-2xl border border-blue-100 bg-blue-50 p-4">
                    <div className="flex items-center gap-2 font-bold text-blue-900">
                      <ShieldCheck size={18} /> Clinician review gate active
                    </div>
                    <p className="mt-2 text-sm leading-6 text-blue-800">
                      This console supports decision review, safety-rule escalation, and auditability. It does not replace clinician judgment.
                    </p>
                  </div>
                </>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
