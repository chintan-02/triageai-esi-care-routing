import { useMemo } from 'react';
import { AlertTriangle, Cpu, FileCheck2, Gauge, ShieldCheck, Timer, Workflow } from 'lucide-react';
import { useAssessmentsStore } from '@/context/AssessmentsContext';
import { useModelStatus } from '@/context/ModelStatusContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { ProbabilityBars } from '@/components/clinical/ProbabilityBars';
import { MetricsBarChart } from '@/components/charts/MetricsBarChart';
import { OperationalTrendChart } from '@/components/charts/OperationalTrendChart';
import { SkeletonStatRow } from '@/components/ui/Skeleton';
import { Button } from '@/components/ui/Button';
import { formatPercent } from '@/lib/formatters';

export function ModelMonitoringPage() {
  const { records } = useAssessmentsStore();
  const { status, isLoading, error, refresh } = useModelStatus();
  const latest = records[0];
  const activeModel = status?.activeModel;
  const metrics = activeModel?.metrics;

  const avgLatency = useMemo(() => Math.round(records.reduce((sum, record) => sum + record.prediction.latencyMs, 0) / Math.max(records.length, 1)), [records]);
  const avgConfidence = useMemo(() => records.reduce((sum, record) => sum + record.prediction.confidence, 0) / Math.max(records.length, 1), [records]);
  const escalations = useMemo(() => records.filter((record) => record.prediction.finalEsi < record.prediction.predictedEsi).length, [records]);

  return (
    <div>
      <PageHeader
        eyebrow="Model operations"
        title="Model Monitoring Console"
        description="Active model status is loaded from a separate model endpoint, while patient predictions stay focused on probabilities, confidence, latency, request ID, safety gate, and recommendation."
        actions={<Button variant="secondary" onClick={() => void refresh()}>Refresh model status</Button>}
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
          <StatCard label="Accuracy" value={formatPercent(metrics?.accuracy)} hint="Final safety-tuned notebook" icon={<Gauge size={22} />} tone="model" />
          <StatCard label="Macro F1" value={formatPercent(metrics?.macroF1)} hint="Class-balance model score" icon={<Workflow size={22} />} tone="blue" />
          <StatCard label="Unsafe 3→5" value={formatPercent(metrics?.unsafeDowngradeRate)} hint="Safety-critical downgrade rate" icon={<ShieldCheck size={22} />} tone="red" />
          <StatCard label="Avg Latency" value={`${avgLatency || 0} ms`} hint="Observed assessment response time" icon={<Timer size={22} />} tone="amber" />
        </div>
      )}

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader title="Current model metadata" description="Loaded from GET /api/v1/model/status, not from a single patient prediction." />
          <CardBody className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Model family / display name</p>
              <p className="mt-1 font-bold text-slate-950">{activeModel?.modelFamily ?? 'Waiting for API data'}</p>
              <p className="mt-1 text-sm font-semibold text-slate-600">{activeModel?.modelDisplayName ?? '—'}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Model version</p>
              <p className="font-data mt-1 font-bold text-slate-950">{activeModel?.modelVersion ?? '—'}</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Feature count</p><p className="font-data mt-1 text-xl font-black text-slate-950">{activeModel?.featureCount ?? '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Deployment threshold</p><p className="font-data mt-1 text-xl font-black text-slate-950">{activeModel?.deploymentThreshold ?? '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">ESI 5 weight</p><p className="font-data mt-1 text-xl font-black text-slate-950">{activeModel?.esi5WeightMultiplier ?? '—'}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Calibration</p><p className="font-data mt-1 text-sm font-black text-slate-950">{activeModel?.calibrationMethod ?? '—'}</p></div>
            </div>
            <div className="rounded-2xl border border-teal-100 bg-teal-50 p-4 text-sm leading-6 text-teal-900">
              <div className="mb-1 flex items-center gap-2 font-bold"><Cpu size={18} /> Final notebook contract</div>
              The active baseline predicts ESI 3/4/5. Safety gate escalation and clinician review handle ESI 1/2 routing. Calibrated probabilities are not deployed unless clinical guardrails pass.
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Final model metric snapshot" description="Safety-tuned source-of-truth values from the executed notebook." />
          <CardBody className="space-y-5">
            <MetricsBarChart metrics={metrics} />
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="flex items-center gap-2 text-sm font-bold text-slate-950"><FileCheck2 size={17} /> Artifact check</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{activeModel?.artifactCheck.checkedAtLabel ?? 'Waiting for model status.'}</p>
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <Card>
          <CardHeader title="Latency & confidence trend" description="Most recent assessments, in submission order." />
          <CardBody><OperationalTrendChart records={records} /></CardBody>
        </Card>

        <Card>
          <CardHeader title="Latest prediction distribution" description="Probability rendering works with any ESI 3/4/5 compatible backend response." />
          <CardBody>
            {latest ? <ProbabilityBars probabilities={latest.prediction.probabilities} /> : <p className="text-sm text-slate-500">No prediction data loaded.</p>}
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Average confidence</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{formatPercent(avgConfidence)}</p></div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Safety escalations</p><p className="font-data mt-1 text-2xl font-black text-slate-950">{escalations}</p></div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
