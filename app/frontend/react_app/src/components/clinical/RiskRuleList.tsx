import { AlertTriangle, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { severityTone } from '@/lib/formatters';
import type { RuleHit } from '@/types/clinical';

export function RiskRuleList({ rules }: { rules: RuleHit[] }) {
  if (!rules.length) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
        <div className="flex items-center gap-2 font-bold">
          <ShieldCheck size={18} />
          No safety-rule escalation triggered
        </div>
        <p className="mt-1 text-emerald-700">The final routing decision still requires clinician review and audit traceability.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {rules.map((rule) => (
        <div key={rule.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="flex gap-3">
              <div className="mt-0.5 rounded-xl bg-red-50 p-2 text-red-700">
                <AlertTriangle size={18} />
              </div>
              <div>
                <h4 className="font-bold text-slate-950">{rule.label}</h4>
                <p className="mt-1 text-sm leading-6 text-slate-600">{rule.description}</p>
              </div>
            </div>
            <Badge className={severityTone(rule.severity)}>{rule.severity}</Badge>
          </div>
          {rule.escalatesTo ? <p className="mt-3 text-xs font-bold uppercase tracking-wide text-red-700">Escalates to ESI {rule.escalatesTo}</p> : null}
        </div>
      ))}
    </div>
  );
}
