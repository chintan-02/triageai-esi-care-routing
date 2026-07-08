import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, AlertTriangle, ArrowUpRight, Clock, FileText, Plus, ShieldCheck } from 'lucide-react';
import { getDashboardSummary } from '@/api/dashboard';
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
import type { DashboardSummaryResponse, RecentAssessmentItem } from '@/types/api';
import type { EsiLevel, ReviewStatus } from '@/types/clinical';

function textOrFallback(value: string | null | undefined, fallback: string): string {
  return value?.trim() || fallback;
}

function isEsiLevel(value: unknown): value is EsiLevel {
  return typeof value === 'number' && [1, 2, 3, 4, 5].includes(value);
}

function normalizeReviewStatus(record: RecentAssessmentItem): ReviewStatus {
  const rawStatus = record.review_status_normalized ?? record.review_status ?? record.clinician_decision ?? record.status;
  if (rawStatus === 'accepted' || rawStatus === 'accept' || rawStatus === 'review_completed') return 'accepted';
  if (rawStatus === 'overridden' || rawStatus === 'override') return 'overridden';
  return 'pending';
}

function displayedFinalEsi(record: RecentAssessmentItem): EsiLevel | null {
  const final = record.clinician_final_esi ?? record.final_esi ?? record.model_final_esi;
  return isEsiLevel(final) ? final : null;
}

function predictedEsi(record: RecentAssessmentItem): EsiLevel | null {
  return isEsiLevel(record.predicted_esi) ? record.predicted_esi : null;
}

function hasSafetyReview(record: RecentAssessmentItem) {
  const predicted = predictedEsi(record);
  const final = displayedFinalEsi(record);
  return record.final_source === 'safety_rule_override' || (predicted !== null && final !== null && final !== predicted);
}

function normalizeDistribution(distribution: Record<string, number>): Record<string, number> {
  return Object.fromEntries(
    Object.entries(distribution).map(([key, value]) => [
      key.startsWith('ESI ') ? key : `ESI ${key}`,
      value
    ])
  );
}

function EsiCell({ level }: { level: EsiLevel | null }) {
  if (!level) return <span className="text-xs font-semibold text-slate-500">N/A</span>;
  return <EsiBadge level={level} />;
}

export function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshSummary = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setSummary(await getDashboardSummary());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Backend request failed.';
      setError(`Unable to load real backend dashboard summary from GET /dashboard/summary. ${message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSummary();
  }, [refreshSummary]);

  const recent = useMemo(
    () =>
      [...(summary?.recent_assessments ?? [])]
        .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))
        .slice(0, 6),
    [summary]
  );

  const stats = useMemo(
    () => ({
      totalAssessments: summary?.total_assessments ?? 0,
      pendingReviews: summary?.pending_reviews ?? 0,
      completedReviews: summary?.completed_reviews ?? summary?.reviewed_assessments ?? 0,
      overrideCount: summary?.override_count ?? 0,
      safetyEscalations: summary?.high_risk_flags ?? 0,
      esiDistribution: normalizeDistribution(summary?.esi_distribution ?? {})
    }),
    [summary]
  );

  const trendPoints = useMemo(
    () =>
      (summary?.recent_assessments ?? []).map((record) => ({
        createdAt: record.created_at,
        latencyMs: record.latency_ms,
        confidence: record.confidence_score
      })),
    [summary]
  );

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
          <StatCard label="Assessments" value={stats.totalAssessments} hint="Loaded from backend database" icon={<Activity size={22} />} tone="blue" />
          <StatCard label="Pending Reviews" value={stats.pendingReviews} hint="Clinician review still required" icon={<Clock size={22} />} tone="amber" />
          <StatCard label="Completed Reviews" value={stats.completedReviews} hint={`${stats.overrideCount} overridden decisions`} icon={<ShieldCheck size={22} />} tone="green" />
          <StatCard label="Safety Escalations" value={stats.safetyEscalations} hint="High-acuity final routing count" icon={<AlertTriangle size={22} />} tone="red" />
        </div>
      )}

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm text-red-800">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span><strong>Could not load dashboard summary.</strong> {error}</span>
            <Button variant="danger" onClick={() => void refreshSummary()} className="px-3 py-2">Retry</Button>
          </div>
        </div>
      ) : null}

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
                    <tr key={record.assessment_id} className="hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <Link to={`/assessments/${record.assessment_id}`} className="font-bold text-slate-950 hover:text-clinical-blue">
                          {textOrFallback(record.patient_name, 'Unknown patient')}
                        </Link>
                        <p className="font-data text-xs text-slate-500">{textOrFallback(record.mrn, 'N/A')}</p>
                      </td>
                      <td className="px-5 py-4">
                        <p className="max-w-[240px] overflow-hidden text-ellipsis text-slate-700 [display:-webkit-box] [-webkit-box-orient:vertical] [-webkit-line-clamp:2]">
                          {record.chief_complaint}
                        </p>
                        {hasSafetyReview(record) ? <p className="mt-1 text-xs font-bold text-red-700">Safety-rule review</p> : null}
                      </td>
                      <td className="px-5 py-4">
                        <EsiCell level={displayedFinalEsi(record)} />
                        <p className="mt-1 text-xs font-semibold text-slate-500">{formatPercent(record.confidence_score ?? undefined)} confidence</p>
                      </td>
                      <td className="px-5 py-4">
                        {typeof record.latency_ms === 'number' ? (
                          <LatencyBadge ms={record.latency_ms} size="sm" />
                        ) : (
                          <span className="text-xs font-semibold text-slate-500">—</span>
                        )}
                      </td>
                      <td className="px-5 py-4">
                        <ReviewStatusBadge status={normalizeReviewStatus(record)} />
                      </td>
                      <td className="px-5 py-4 text-slate-500">{formatDateTime(record.created_at)}</td>
                      <td className="px-5 py-4 text-right">
                        <Link to={`/assessments/${record.assessment_id}`}>
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
                  <OperationalTrendChart points={trendPoints} />
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
