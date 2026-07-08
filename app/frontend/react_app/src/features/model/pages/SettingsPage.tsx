import { AlertTriangle, Database, LockKeyhole, PlugZap, ServerCog, type LucideIcon } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useModelStatus } from '@/context/ModelStatusContext';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { API_BASE_URL, USE_MOCK_API, getRuntimeWarnings } from '@/lib/env';
import { roleSummary } from '@/lib/permissions';

const checklist: Array<{ icon: LucideIcon; title: string; description: string }> = [
  { icon: ServerCog, title: 'Assessment endpoints', description: 'GET /assessments, GET /assessments/{id}, and POST /predict persist backend assessment data.' },
  { icon: PlugZap, title: 'Prediction service', description: 'POST /predict runs the backend LightGBM V2 decision-support workflow and stores audit-ready records.' },
  { icon: Database, title: 'Readiness and dashboard', description: 'GET /ready and GET /dashboard/summary report backend/database/model state from the source of truth.' },
  { icon: LockKeyhole, title: 'RBAC/auth', description: 'Local auth is development-only. Production should use FastAPI JWT or secure httpOnly session auth for Admin, Doctor, and Nurse permissions.' }
];

const warningTone = {
  info: 'border-blue-200 bg-blue-50 text-blue-800',
  warning: 'border-amber-200 bg-amber-50 text-amber-800',
  critical: 'border-red-200 bg-red-50 text-red-800'
};

export function SettingsPage() {
  const { user } = useAuth();
  const { readiness } = useModelStatus();
  const runtimeWarnings = getRuntimeWarnings();

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
              <div className="mt-2"><Badge className="border-blue-200 bg-blue-50 text-blue-800">{USE_MOCK_API ? 'development mock' : 'backend connected'}</Badge></div>
              <p className="font-data mt-2 text-xs font-semibold text-slate-500">Base URL: {API_BASE_URL}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Signed in as</p>
              <p className="mt-1 font-bold text-slate-950">{user?.name ?? '—'}</p>
              <p className="text-sm text-slate-500">{user?.role ?? ''}</p>
              {user ? <p className="mt-2 text-xs leading-5 text-slate-500">{roleSummary(user.role)}</p> : null}
            </div>
            <div className="space-y-2">
              {runtimeWarnings.map((warning) => (
                <div key={warning.id} className={`rounded-2xl border p-4 text-sm leading-6 ${warningTone[warning.severity]}`}>
                  <div className="flex gap-2 font-bold"><AlertTriangle size={17} /> {warning.title}</div>
                  <p className="mt-1">{warning.detail}</p>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-700">
              Backend-connected data mode is the default. Use{' '}
              <code className="rounded bg-slate-100 px-1.5 py-1 text-xs font-bold">VITE_API_BASE_URL=http://localhost:8001</code> for local FastAPI, and only set{' '}
              <code className="rounded bg-slate-100 px-1.5 py-1 text-xs font-bold">VITE_USE_MOCK_API=true</code> for isolated UI development with synthetic records.
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
        <CardHeader title="Final model source of truth" description="Values loaded from backend readiness and the configured model registry." />
        <CardBody className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[
            ['Model', readiness?.model_name ?? '—'],
            ['Model version', readiness?.model_version ?? '—'],
            ['Model source', readiness?.model_source ?? '—'],
            ['Feature Count', readiness?.feature_count ? String(readiness.feature_count) : '—'],
            ['Calibration', readiness?.selected_calibration_method ?? '—'],
            ['Threshold config', readiness?.threshold_config_loaded ? 'Loaded' : '—'],
            ['Class Order', readiness?.class_order?.join(', ') ?? '—'],
            ['Placeholder', readiness ? String(readiness.is_placeholder) : '—']
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
