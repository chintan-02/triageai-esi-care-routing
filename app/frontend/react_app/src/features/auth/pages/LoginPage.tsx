import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  BadgeCheck,
  Eye,
  EyeOff,
  Loader2,
  LockKeyhole,
  LogIn,
  ShieldCheck,
  Stethoscope,
  UserPlus
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { LOCAL_DEV_PASSWORD } from '@/api/authApi';
import { roleSummary } from '@/lib/permissions';
import type { ClinicianRole } from '@/types/auth';

const roles: ClinicianRole[] = ['Nurse', 'Doctor', 'Admin'];
type AuthMode = 'sign-in' | 'sign-up';

const inputClass = 'focus-ring w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 placeholder:text-slate-400';
const labelClass = 'block space-y-2 text-sm font-semibold text-slate-700';

function ProductMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3">
      <p className="text-[0.65rem] font-extrabold uppercase tracking-[0.18em] text-blue-100/70">{label}</p>
      <p className="mt-1 font-display text-lg font-extrabold text-white">{value}</p>
    </div>
  );
}

export function LoginPage() {
  const { user, login, register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState<AuthMode>('sign-in');
  const [identifier, setIdentifier] = useState('');
  const [signInRole, setSignInRole] = useState<ClinicianRole>('Nurse');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [signUpRole, setSignUpRole] = useState<ClinicianRole>('Nurse');
  const [accessCode, setAccessCode] = useState('');
  const [showAccessCode, setShowAccessCode] = useState(false);

  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) {
    const redirectFrom = (location.state as { from?: string } | null)?.from;
    const redirectTo = redirectFrom && redirectFrom !== '/' ? redirectFrom : '/command-center';
    return <Navigate to={redirectTo} replace />;
  }

  const submitSignIn = async () => {
    if (!identifier.trim()) {
      setError('Enter your name or work email to continue.');
      return;
    }
    await login(identifier, signInRole, password);
    showToast({ tone: 'success', title: 'Signed in', description: `Welcome back, ${identifier.trim()}.` });
    navigate('/command-center', { replace: true });
  };

  const submitSignUp = async () => {
    await register({
      name,
      email,
      organization: '',
      unit: '',
      role: signUpRole,
      password: accessCode
    });
    showToast({ tone: 'success', title: 'Account created', description: `${name.trim()} now has ${signUpRole} access in local mode.` });
    navigate('/command-center', { replace: true });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      if (mode === 'sign-in') await submitSignIn();
      else await submitSignUp();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to continue.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_rgba(248,250,252,0.9),_transparent_45%),linear-gradient(135deg,#f8fafc_0%,#eef4ff_100%)] p-4 sm:p-6 lg:p-8">
      <section className="grid min-h-[720px] w-full max-w-6xl overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-[0_30px_90px_rgba(15,23,42,0.10)] lg:grid-cols-[0.95fr_1.05fr]">
        <aside className="relative hidden overflow-hidden bg-clinical-navy text-white lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_22%_18%,rgba(37,99,235,0.28),transparent_28rem),radial-gradient(circle_at_82%_78%,rgba(13,148,136,0.20),transparent_26rem)]" />
          <div className="clinical-grid absolute inset-0 opacity-35" />
          <div className="relative flex h-full flex-col justify-between p-10 xl:p-12">
            <div>
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
                  <Activity size={26} />
                </div>
                <div>
                  <p className="font-display text-xl font-extrabold tracking-tight">TriageAI</p>
                  <p className="text-sm text-blue-100/80">Clinical Intake Console</p>
                </div>
              </div>

              <div className="mt-14 max-w-xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-blue-300/20 bg-blue-400/10 px-3 py-1 text-[0.68rem] font-extrabold uppercase tracking-[0.2em] text-blue-100">
                  <Stethoscope size={14} /> Human-in-the-loop ESI workflow
                </div>
                <h1 className="font-display mt-6 text-3.5xl font-extrabold leading-tight xl:text-4.5xl">
                  Structured emergency intake for safer ESI care routing.
                </h1>
                <p className="mt-4 max-w-lg text-sm leading-6 text-slate-300">
                  A calm clinical workspace for structured intake, safety-rule escalation, clinician review, audit history, and PDF decision-support summaries.
                </p>
              </div>

              <div className="mt-9 grid max-w-xl grid-cols-3 gap-3">
                <ProductMetric label="Model scope" value="ESI 3/4/5" />
                <ProductMetric label="Safety gate" value="Rules + review" />
                <ProductMetric label="Evidence" value="Audit ready" />
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/8 p-5 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 rounded-2xl bg-emerald-400/10 p-2 text-emerald-200 ring-1 ring-emerald-300/20">
                  <ShieldCheck size={19} />
                </div>
                <div>
                  <p className="font-bold text-white">Not a diagnostic tool</p>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    Model output is treated as decision support. Safety rules and clinician review remain the final control layer before routing.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <section className="flex items-center justify-center bg-[linear-gradient(135deg,#ffffff,#f8fbff)] p-5 sm:p-8 lg:p-10">
          <div className="w-full max-w-[430px]">
            <div className="mb-7 flex items-center justify-between lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-clinical-navy text-white">
                  <Activity size={21} />
                </div>
                <div>
                  <p className="font-display text-lg font-extrabold text-slate-950">TriageAI</p>
                  <p className="text-xs font-medium text-slate-500">Clinical Intake Console</p>
                </div>
              </div>
            </div>

            <div className="mb-5 rounded-2xl border border-blue-100 bg-blue-50/80 px-4 py-3 text-xs leading-5 text-blue-900">
              <strong>Local product mode:</strong> sign in instantly or create a local account for workflow testing. Production should use backend auth, role approval, and secure sessions.
            </div>

            <form onSubmit={submit} className="rounded-[1.75rem] border border-slate-200/80 bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.06)] sm:p-7">
              <div className="flex rounded-2xl border border-slate-200 bg-slate-50 p-1">
                <button
                  type="button"
                  onClick={() => {
                    setMode('sign-in');
                    setError('');
                  }}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-extrabold transition ${
                    mode === 'sign-in' ? 'bg-clinical-navy text-white shadow-card' : 'text-slate-500 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  <LogIn size={16} /> Sign in
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode('sign-up');
                    setError('');
                  }}
                  className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-extrabold transition ${
                    mode === 'sign-up' ? 'bg-clinical-navy text-white shadow-card' : 'text-slate-500 hover:bg-white hover:text-slate-900'
                  }`}
                >
                  <UserPlus size={16} /> Create account
                </button>
              </div>

              <div className="mt-7">
                <p className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-extrabold uppercase tracking-[0.14em] text-emerald-700">
                  <BadgeCheck size={14} /> Secure clinical access
                </p>
                <h2 className="font-display mt-4 text-2xl font-extrabold tracking-tight text-slate-950">
                  {mode === 'sign-in' ? 'Welcome back' : 'Create local account'}
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {mode === 'sign-in'
                    ? 'Access the ESI intake console using your local account or the development access code.'
                    : 'Set up a local account profile for role-based workflow testing before backend auth is connected.'}
                </p>
              </div>

              <div className="mt-6 space-y-4">
                {mode === 'sign-in' ? (
                  <>
                    <label className={labelClass}>
                      Name or work email
                      <input
                        value={identifier}
                        onChange={(event) => setIdentifier(event.target.value)}
                        placeholder="Example: priya.nair@hospital.ca"
                        className={inputClass}
                        autoFocus
                      />
                    </label>

                    <label className={labelClass}>
                      Role for local fallback access
                      <select value={signInRole} onChange={(event) => setSignInRole(event.target.value as ClinicianRole)} className={inputClass}>
                        {roles.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className={labelClass}>
                      Password / local access code
                      <div className="flex rounded-2xl border border-slate-200 bg-white">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          value={password}
                          onChange={(event) => setPassword(event.target.value)}
                          placeholder={LOCAL_DEV_PASSWORD}
                          className="focus-ring min-w-0 flex-1 rounded-l-2xl bg-transparent px-4 py-3 text-sm font-medium text-slate-900 placeholder:text-slate-400"
                        />
                        <button type="button" onClick={() => setShowPassword((v) => !v)} className="flex items-center rounded-r-2xl px-3 text-slate-400 hover:text-slate-600">
                          {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                        </button>
                      </div>
                    </label>

                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-600">
                      <strong className="text-slate-800">{signInRole} access:</strong> {roleSummary(signInRole)}
                    </div>
                  </>
                ) : (
                  <>
                    <label className={labelClass}>
                      Full name
                      <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Priya Nair" className={inputClass} autoFocus />
                    </label>

                    <label className={labelClass}>
                      Work email
                      <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="priya.nair@hospital.ca" className={inputClass} />
                    </label>

                    <label className={labelClass}>
                      Role
                      <select value={signUpRole} onChange={(event) => setSignUpRole(event.target.value as ClinicianRole)} className={inputClass}>
                        {roles.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className={labelClass}>
                      Local access code
                      <div className="flex rounded-2xl border border-slate-200 bg-white">
                        <span className="flex items-center pl-4 text-slate-400"><LockKeyhole size={17} /></span>
                        <input
                          type={showAccessCode ? 'text' : 'password'}
                          value={accessCode}
                          onChange={(event) => setAccessCode(event.target.value)}
                          placeholder={LOCAL_DEV_PASSWORD}
                          className="focus-ring min-w-0 flex-1 bg-transparent px-3 py-3 text-sm font-medium text-slate-900 placeholder:text-slate-400"
                        />
                        <button type="button" onClick={() => setShowAccessCode((v) => !v)} className="flex items-center rounded-r-2xl px-3 text-slate-400 hover:text-slate-600">
                          {showAccessCode ? <EyeOff size={17} /> : <Eye size={17} />}
                        </button>
                      </div>
                    </label>

                    <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-3 text-xs leading-5 text-emerald-800">
                      <strong>Approval note:</strong> in production this should create a pending account that an Admin approves before access is granted.
                    </div>
                  </>
                )}

                {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">{error}</p> : null}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="focus-ring flex w-full items-center justify-center gap-2 rounded-2xl bg-clinical-navy px-4 py-3.5 text-sm font-extrabold text-white transition hover:-translate-y-0.5 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-clinical-blue focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? <Loader2 size={18} className="animate-spin" /> : mode === 'sign-in' ? <LogIn size={18} /> : <UserPlus size={18} />}
                  {mode === 'sign-in' ? 'Sign in' : 'Create account'}
                </button>
              </div>
            </form>
          </div>
        </section>
      </section>
    </main>
  );
}
