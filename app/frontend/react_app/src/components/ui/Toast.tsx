import { CheckCircle2, Info, X, XCircle } from 'lucide-react';
import { useToast } from '@/context/ToastContext';

const toneStyles = {
  success: { border: 'border-emerald-200', bg: 'bg-emerald-50', icon: 'text-emerald-600', Icon: CheckCircle2 },
  error: { border: 'border-red-200', bg: 'bg-red-50', icon: 'text-red-600', Icon: XCircle },
  info: { border: 'border-blue-200', bg: 'bg-blue-50', icon: 'text-blue-600', Icon: Info }
};

export function ToastViewport() {
  const { toasts, dismissToast } = useToast();

  if (!toasts.length) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-center gap-3 p-4 sm:items-end sm:p-6">
      {toasts.map((toast) => {
        const style = toneStyles[toast.tone];
        const Icon = style.Icon;
        return (
          <div
            key={toast.id}
            className={`animate-toast-in pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-2xl border ${style.border} ${style.bg} p-4 shadow-pop`}
          >
            <Icon size={20} className={`mt-0.5 shrink-0 ${style.icon}`} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-950">{toast.title}</p>
              {toast.description ? <p className="mt-0.5 text-sm leading-5 text-slate-600">{toast.description}</p> : null}
            </div>
            <button onClick={() => dismissToast(toast.id)} className="focus-ring shrink-0 rounded-lg p-1 text-slate-400 hover:bg-black/5 hover:text-slate-600">
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
