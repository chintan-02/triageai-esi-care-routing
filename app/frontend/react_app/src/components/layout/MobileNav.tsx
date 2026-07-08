import { NavLink } from 'react-router-dom';
import { Activity, X } from 'lucide-react';
import { navItems } from './navItems';
import { useAuth } from '@/context/AuthContext';
import { hasPermission } from '@/lib/permissions';

export function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user } = useAuth();
  const visibleNavItems = navItems.filter((item) => !item.permission || hasPermission(user?.role, item.permission));

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <div className="absolute inset-0 bg-slate-950/50" onClick={onClose} aria-hidden="true" />
      <div className="absolute inset-y-0 left-0 flex w-72 flex-col bg-clinical-navy p-5 text-white shadow-pop">
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
              <Activity size={22} />
            </div>
            <div>
              <p className="font-display text-lg font-extrabold tracking-tight">TriageAI</p>
              <p className="text-xs font-medium text-blue-100/80">Clinical Intake Console</p>
            </div>
          </div>
          <button onClick={onClose} className="focus-ring rounded-xl p-2 text-slate-200 hover:bg-white/10" aria-label="Close navigation">
            <X size={20} />
          </button>
        </div>
        <nav className="space-y-1">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/command-center'}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                    isActive ? 'bg-white text-clinical-navy shadow-soft' : 'text-slate-200 hover:bg-white/10 hover:text-white'
                  }`
                }
              >
                <Icon size={19} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
