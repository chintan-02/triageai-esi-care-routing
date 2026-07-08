/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { getReady } from '@/api/health';
import type { ReadyResponse } from '@/types/api';

interface ModelStatusContextValue {
  readiness: ReadyResponse | null;
  isLoading: boolean;
  isReadinessLoading: boolean;
  error: string | null;
  readinessError: string | null;
  refresh: () => Promise<void>;
  refreshReadiness: () => Promise<void>;
}

const ModelStatusContext = createContext<ModelStatusContextValue | null>(null);

export function ModelStatusProvider({ children }: { children: ReactNode }) {
  const [readiness, setReadiness] = useState<ReadyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReadinessLoading, setIsReadinessLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [readinessError, setReadinessError] = useState<string | null>(null);

  const refreshReadiness = useCallback(async () => {
    setIsReadinessLoading(true);
    setReadinessError(null);
    try {
      setReadiness(await getReady());
    } catch (err) {
      setReadiness(null);
      setReadinessError(err instanceof Error ? err.message : 'Backend readiness is unavailable.');
    } finally {
      setIsReadinessLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      await refreshReadiness();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load backend model readiness.');
    } finally {
      setIsLoading(false);
    }
  }, [refreshReadiness]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({ readiness, isLoading, isReadinessLoading, error, readinessError, refresh, refreshReadiness }),
    [readiness, isLoading, isReadinessLoading, error, readinessError, refresh, refreshReadiness]
  );

  return <ModelStatusContext.Provider value={value}>{children}</ModelStatusContext.Provider>;
}

export function useModelStatus() {
  const ctx = useContext(ModelStatusContext);
  if (!ctx) throw new Error('useModelStatus must be used within ModelStatusProvider');
  return ctx;
}
