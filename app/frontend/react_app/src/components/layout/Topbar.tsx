import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, LogOut, Menu, Search, ServerCog } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useModelStatus } from '@/context/ModelStatusContext';
import { roleSummary } from '@/lib/permissions';

function compactModelName(modelName?: string | null) {
  if (!modelName) return 'Model ready';
  if (modelName.toLowerCase().includes('lightgbm v2')) return 'LightGBM V2';
  return modelName;
}

export function Topbar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const { user, logout } = useAuth();
  const { readiness, isReadinessLoading, readinessError } = useModelStatus();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState('');

  const backendConnected = Boolean(readiness && readiness.model_loaded && !readiness.is_placeholder);
  const modelUnavailable = Boolean(readiness && (!readiness.model_loaded || readiness.is_placeholder));
  const statusLabel = backendConnected ? 'Backend connected' : modelUnavailable ? 'Model unavailable' : isReadinessLoading ? 'Checking API' : 'API offline';
  const statusDetail = backendConnected ? compactModelName(readiness?.model_name) : modelUnavailable ? 'Model not loaded' : 'FastAPI unavailable';
  const statusTitle = backendConnected
    ? `Final model: ${readiness?.model_name ?? 'Unavailable'}\nVersion: ${readiness?.model_version ?? 'Unavailable'}`
    : readinessError ?? 'Waiting for backend readiness.';
  const statusClass = backendConnected
    ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
    : modelUnavailable
      ? 'border-amber-200 bg-amber-50 text-amber-800'
      : 'border-red-200 bg-red-50 text-red-800';

  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed) navigate(`/assessments?search=${encodeURIComponent(trimmed)}`);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 px-4 py-3 shadow-[0_10px_30px_rgba(15,23,42,0.04)] backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button onClick={onOpenMenu} className="focus-ring rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:bg-slate-50 lg:hidden" aria-label="Open navigation">
          <Menu size={20} />
        </button>

        <form onSubmit={submitSearch} className="hidden items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-500 shadow-sm md:flex md:w-[min(30rem,100%)]">
          <Search size={18} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="min-w-0 flex-1 bg-transparent font-medium outline-none placeholder:text-slate-400"
            placeholder="Search patient, MRN, complaint, assessment, report..."
          />
        </form>

        <div className="ml-auto flex items-center gap-2 sm:gap-3">
          <div
            className={`hidden items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] sm:flex ${statusClass}`}
            title={statusTitle}
          >
            <ServerCog size={14} />
            <span className="flex flex-col leading-tight">
              <span>{statusLabel}</span>
              <span className="font-bold tracking-[0.08em] opacity-80">{statusDetail}</span>
            </span>
          </div>
          <button className="focus-ring flex h-10 w-10 items-center justify-center rounded-2xl border border-slate-200 bg-white text-slate-600 shadow-sm hover:bg-slate-50" aria-label="Notifications">
            <Bell size={18} />
          </button>

          <div className="relative">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="focus-ring flex items-center gap-2.5 rounded-2xl border border-slate-200 bg-white px-2.5 py-2 shadow-sm hover:bg-slate-50 sm:px-3"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-clinical-navy text-sm font-black text-white">{user?.initials ?? '—'}</div>
              <div className="hidden text-left sm:block">
                <p className="text-sm font-bold text-slate-950">{user?.name ?? 'Signed out'}</p>
                <p className="text-xs text-slate-500">{user?.role ?? ''}</p>
              </div>
            </button>
            {menuOpen ? (
              <div className="absolute right-0 z-30 mt-2 w-72 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-pop">
                {user ? (
                  <div className="border-b border-slate-100 px-4 py-3">
                    <p className="text-sm font-bold text-slate-950">{user.role} permissions</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{roleSummary(user.role)}</p>
                  </div>
                ) : null}
                <button
                  onClick={() => void logout()}
                  className="focus-ring flex w-full items-center gap-2 px-4 py-3 text-left text-sm font-semibold text-red-700 hover:bg-red-50"
                >
                  <LogOut size={16} /> Sign out
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
