import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production, forward this to your monitoring stack (Sentry, Azure App
    // Insights, etc). Kept as a console log here since this is a frontend-only build.
    console.error('TriageAI UI crashed:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-clinical-surface p-6">
          <div className="max-w-md rounded-3xl border border-red-200 bg-white p-8 text-center shadow-pop">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
              <AlertTriangle size={26} />
            </div>
            <h1 className="font-display mt-4 text-lg font-bold text-slate-950">Something went wrong</h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The console UI hit an unexpected error. This does not affect any stored assessment data.
            </p>
            <button
              onClick={() => window.location.assign('/')}
              className="focus-ring mt-5 inline-flex items-center gap-2 rounded-xl bg-clinical-navy px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              <RotateCcw size={16} /> Reload console
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
