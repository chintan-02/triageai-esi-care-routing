import { NavLink } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { navItems } from './navItems';
import { useAuth } from '@/context/AuthContext';
import { hasPermission } from '@/lib/permissions';

export function Sidebar() {
  const { user } = useAuth();
  const visibleNavItems = navItems.filter((item) => !item.permission || hasPermission(user?.role, item.permission));

  return (
    <aside className="hidden w-72 shrink-0 border-r border-white/10 bg-gradient-to-b from-slate-950 via-clinical-navy to-slate-900 p-5 text-white shadow-[12px_0_40px_rgba(15,23,42,0.16)] lg:flex lg:flex-col lg:sticky lg:top-0 lg:h-screen">
      <div className="mb-7 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
          <Activity size={24} />
        </div>
        <div>
          <p className="font-display text-lg font-extrabold tracking-tight">TriageAI</p>
          <p className="text-xs font-medium text-blue-100/80">Clinical Intake Console</p>
        </div>
      </div>

      <nav className="space-y-1.5">
        {visibleNavItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/command-center'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition ${
                  isActive ? 'bg-white text-clinical-navy shadow-soft' : 'text-slate-200 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/10 p-3.5 backdrop-blur-sm">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-blue-100/70">Safety mode</p>
        <p className="mt-1.5 text-sm font-semibold">Human-in-the-loop enabled</p>
        <p className="mt-1.5 text-xs leading-5 text-slate-300">Structured intake and clinician review remain in the workflow before final use.</p>
      </div>
    </aside>
  );
}
