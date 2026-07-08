/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { apiClient } from '@/api/apiClient';
import type { ModelStatusResponse } from '@/types/clinical';

interface ModelStatusContextValue {
  status: ModelStatusResponse | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const ModelStatusContext = createContext<ModelStatusContextValue | null>(null);

export function ModelStatusProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<ModelStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setStatus(await apiClient.getModelStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load model status.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(() => ({ status, isLoading, error, refresh }), [status, isLoading, error, refresh]);

  return <ModelStatusContext.Provider value={value}>{children}</ModelStatusContext.Provider>;
}

export function useModelStatus() {
  const ctx = useContext(ModelStatusContext);
  if (!ctx) throw new Error('useModelStatus must be used within ModelStatusProvider');
  return ctx;
}
