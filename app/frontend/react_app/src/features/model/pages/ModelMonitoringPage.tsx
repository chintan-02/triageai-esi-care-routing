import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Cpu, FileCheck2, Gauge, ShieldCheck, Timer, Workflow } from 'lucide-react';
import { getDashboardSummary } from '@/api/dashboard';
import { useModelStatus } from '@/context/ModelStatusContext';
import type { DashboardSummaryResponse, RecentAssessmentItem } from '@/types/api';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { MetricsBarChart } from '@/components/charts/MetricsBarChart';
import { OperationalTrendChart } from '@/components/charts/OperationalTrendChart';
import { SkeletonStatRow } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import { formatPercent } from '@/lib/formatters';

function latestAssessment(records: RecentAssessmentItem[]): RecentAssessmentItem | null {
  return [...records].sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))[0] ?? null;
}

export function ModelMonitoringPage() {
  const { readiness, isLoading: isModelLoading, error: modelError, readinessError, refresh } = useModelStatus();
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const refreshSummary = useCallback(async () => {
    setIsSummaryLoading(true);
    setSummaryError(null);
    try {
      setSummary(await getDashboardSummary());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Backend request failed.';
      setSummaryError(`Unable to load operational model signals from GET /dashboard/summary. ${message}`);
    } finally {
      setIsSummaryLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSummary();
  }, [refreshSummary]);

  const recent = useMemo(() => summary?.recent_assessments ?? [], [summary]);
  const latest = useMemo(() => latestAssessment(recent), [recent]);
  const avgLatency = useMemo(() => {
    const latencies = recent.map((record) => record.latency_ms).filter((value): value is number => typeof value === 'number');
    return latencies.length ? Math.round(latencies.reduce((sum, value) => sum + value, 0) / latencies.length) : null;
  }, [recent]);
  const avgConfidence = useMemo(() => {
    const confidences = recent.map((record) => record.confidence_score).filter((value): value is number => typeof value === 'number');
    return confidences.length ? confidences.reduce((sum, value) => sum + value, 0) / confidences.length : undefined;
  }, [recent]);
  const isLoading = isModelLoading || isSummaryLoading;
  const error = modelError ?? readinessError ?? summaryError;
  const backendReady = Boolean(readiness && readiness.database_connected && readiness.model_loaded && !readiness.is_placeholder);

  return (
    <div>
      <PageHeader
        eyebrow="Model operations"
        title="Model Monitoring Console"
        description="Active model readiness is loaded from the backend /ready endpoint, while operational signals come from stored backend assessments."
        actions={<Button variant="secondary" onClick={() => { void refresh(); void refreshSummary(); }}>Refresh model status</Button>}
      />

      {error ? (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardBody className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex gap-3 text-red-800"><AlertTriangle size={22} /><div><p className="font-bold">Model status unavailable</p><p className="text-sm">{error}</p></div></div>
            <Button variant="danger" onClick={() => void refresh()}>Retry</Button>
          </CardBody>
        </Card>
      ) : null}

      {isLoading ? (
        <SkeletonStatRow />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Backend" value={backendReady ? 'Ready' : 'Unavailable'} hint={readiness?.database ?? 'FastAPI readiness'} icon={<Gauge size={22} />} tone="model" />
          <StatCard label="Model Loaded" value={readiness?.model_loaded ? 'Yes' : 'No'} hint={readiness?.model_source ?? 'Model registry source'} icon={<Workflow size={22} />} tone="blue" />
          <StatCard label="Placeholders" value={readiness?.is_placeholder ? 'Yes' : 'No'} hint="Backend /ready placeholder flag" icon={<ShieldCheck size={22} />} tone="red" />
          <StatCard label="Avg Latency" value={avgLatency === null ? '—' : `${avgLatency} ms`} hint="Observed assessment response time" icon={<Timer size={22} />} tone="amber" />
        </div>
      )}

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader title="Current model metadata" description="Loaded from GET /ready and the backend model registry." />
          <CardBody className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Model family / display name</p>
              <p className="mt-1 font-bold text-slate-950">{readiness?.model_name ?? 'Waiting for backend readiness'}</p>
              <p className="mt-1 text-sm font-semibold text-slate-600">{readiness?.model_source ?? '—'}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Model version</p>
              <p className="font-data mt-1 font-bold text-slate-950">{readiness?.model_version ?? '—'}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Feature count</p><p className="font-data mt-1 text-xl font-black text-slate-950">{readiness?.feature_count ?? '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Threshold config</p><p className="font-data mt-1 text-xl font-black text-slate-950">{readiness?.threshold_config_loaded ? 'Loaded' : '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Class order</p><p className="font-data mt-1 text-sm font-black text-slate-950">{readiness?.class_order?.join(', ') ?? '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Calibration</p><p className="font-data mt-1 text-sm font-black text-slate-950">{readiness?.selected_calibration_method ?? '—'}</p></div>
            </div>
            <div className="rounded-2xl border border-teal-100 bg-teal-50 p-4 text-sm leading-6 text-teal-900">
              <div className="mb-1 flex items-center gap-2 font-bold"><Cpu size={18} /> Final notebook contract</div>
              The active baseline predicts ESI 3/4/5. Safety gate escalation and clinician review handle ESI 1/2 routing. Calibrated probabilities are not deployed unless clinical guardrails pass.
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Backend model readiness" description="Live readiness fields from the backend source of truth." />
          <CardBody className="space-y-5">
            <MetricsBarChart />
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="flex items-center gap-2 text-sm font-bold text-slate-950"><FileCheck2 size={17} /> Artifact check</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {readiness?.model_error ? readiness.model_error : readiness?.model_loaded ? 'Backend model artifacts are loaded from the configured model registry.' : 'Waiting for backend readiness.'}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <Card>
          <CardHeader title="Latency & confidence trend" description="Most recent assessments, in submission order." />
          <CardBody>
            <OperationalTrendChart
              points={recent.map((record) => ({
                createdAt: record.created_at,
                latencyMs: record.latency_ms,
                confidence: record.confidence_score
              }))}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Latest prediction distribution" description="Probability rendering works with any ESI 3/4/5 compatible backend response." />
          <CardBody>
            {latest ? (
              <p className="text-sm leading-6 text-slate-600">
                Latest assessment-level probabilities are available in Assessment Detail. This panel uses backend summary data only, so it does not display synthetic probability bars.
              </p>
            ) : (
              <p className="text-sm text-slate-500">No prediction data loaded.</p>
            )}
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Average confidence</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{formatPercent(avgConfidence)}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">High-risk final routing</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{summary?.high_risk_flags ?? 0}</p></div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
