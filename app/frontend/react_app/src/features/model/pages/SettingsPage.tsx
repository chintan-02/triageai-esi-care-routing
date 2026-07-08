import { AlertTriangle, Database, LockKeyhole, PlugZap, ServerCog, type LucideIcon } from 'lucide-react';
import { apiClient } from '@/api/apiClient';
import { useAuth } from '@/context/AuthContext';
import { useModelStatus } from '@/context/ModelStatusContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { roleSummary } from '@/lib/permissions';

const checklist: Array<{ icon: LucideIcon; title: string; description: string }> = [
  { icon: ServerCog, title: 'Assessment adapter endpoints', description: 'GET /api/v1/assessments, POST /api/v1/assessments, POST /api/v1/assessments/{id}/review' },
  { icon: PlugZap, title: 'Prediction adapter', description: 'Adapter calls your existing /predict service internally, applies the safety gate, saves audit data, then returns AssessmentRecord.' },
  { icon: Database, title: 'Model status endpoint', description: 'GET /api/v1/model/status returns final notebook metrics, threshold, feature count, calibration decision, and artifact-check status.' },
  { icon: LockKeyhole, title: 'RBAC/auth', description: 'FastAPI JWT or secure httpOnly session auth for Admin, Doctor, and Nurse permissions.' }
];

const warningTone = {
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-800'
};

export function SettingsPage() {
  const { user } = useAuth();
  const { status } = useModelStatus();
  const activeModel = status?.activeModel;

  return (
    <div>
      <PageHeader
        eyebrow="System configuration"
        title="Frontend Integration Settings"
        description="Production-readiness checklist for connecting this React frontend to FastAPI, the final model registry, reports, audit logs, and role-based auth."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Runtime mode" description="Standalone mode is for local development only. Real deployment should use live API and backend auth." />
          <CardBody className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Current API mode</p>
              <div className="mt-2"><Badge className="border-blue-200 bg-blue-50 text-blue-800">{apiClient.mode}</Badge></div>
              <p className="font-data mt-2 text-xs font-semibold text-slate-500">Base URL: {apiClient.baseUrl}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Signed in as</p>
              <p className="mt-1 font-bold text-slate-950">{user?.name ?? '—'}</p>
              <p className="text-sm text-slate-500">{user?.role ?? ''}</p>
              {user ? <p className="mt-2 text-xs leading-5 text-slate-500">{roleSummary(user.role)}</p> : null}
            </div>
            <div className="space-y-2">
              {apiClient.runtimeWarnings.map((warning) => (
                <div key={warning.id} className={`rounded-2xl border p-4 text-sm leading-6 ${warningTone[warning.severity]}`}>
                  <div className="flex gap-2 font-bold"><AlertTriangle size={17} /> {warning.title}</div>
                  <p className="mt-1">{warning.detail}</p>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-700">
              Use <code className="rounded bg-slate-100 px-1.5 py-1 text-xs font-bold">VITE_USE_MOCK_API=false</code>,{' '}
              <code className="rounded bg-slate-100 px-1.5 py-1 text-xs font-bold">VITE_USE_MOCK_AUTH=false</code>, and{' '}
              <code className="rounded bg-slate-100 px-1.5 py-1 text-xs font-bold">VITE_API_BASE_URL=http://localhost:8000</code> when the backend adapter and auth routes are ready.
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Integration checklist" description="What to connect when you drop this into the main repo." />
          <CardBody className="space-y-3">
            {checklist.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.title} className="flex gap-3 rounded-2xl border border-slate-200 bg-white p-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><Icon size={19} /></div>
                  <div><p className="font-bold text-slate-950">{item.title}</p><p className="mt-1 text-sm text-slate-600">{item.description}</p></div>
                </div>
              );
            })}
          </CardBody>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Final model source of truth" description="Values loaded from the model-status contract, based on the final executed notebook you provided." />
        <CardBody className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ['Notebook', activeModel?.sourceNotebook ?? '—'],
            ['Model', activeModel?.modelDisplayName ?? '—'],
            ['Threshold', activeModel ? String(activeModel.deploymentThreshold) : '—'],
            ['Feature Count', activeModel ? String(activeModel.featureCount) : '—'],
            ['Calibration', activeModel?.calibrationMethod ?? '—'],
            ['Calibrated deployed', activeModel ? String(activeModel.deployCalibratedProbabilities) : '—'],
            ['Class Scope', activeModel?.classScope ?? '—'],
            ['Artifact Check', activeModel?.artifactCheck.status ?? '—']
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-black uppercase tracking-wide text-slate-500">{label}</p>
              <p className="font-data mt-2 break-words text-sm font-bold text-slate-950">{value}</p>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  );
}
