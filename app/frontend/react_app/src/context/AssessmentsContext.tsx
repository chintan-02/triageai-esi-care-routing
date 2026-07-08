// This file exports both the provider component and its `useX` hook, which is
// the standard React context pattern. react-refresh's export-purity rule flags
// that combination; disabled here rather than splitting one small file in two.
/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { apiClient } from '@/api/apiClient';
import type { AssessmentRecord, ClinicianReview, DashboardSummary, IntakePayload } from '@/types/clinical';
import { buildDashboardSummary } from '@/data/mockData';

interface AssessmentsContextValue {
  records: AssessmentRecord[];
  summary: DashboardSummary | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  createAssessment: (payload: IntakePayload) => Promise<AssessmentRecord>;
  saveReview: (id: string, review: ClinicianReview) => Promise<AssessmentRecord | undefined>;
}

const AssessmentsContext = createContext<AssessmentsContextValue | null>(null);

export function AssessmentsProvider({ children }: { children: ReactNode }) {
  const [records, setRecords] = useState<AssessmentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const loaded = await apiClient.listAssessments();
      setRecords(loaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load assessments.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const createAssessment = useCallback(async (payload: IntakePayload) => {
    setError(null);
    const record = await apiClient.createAssessment(payload);
    setRecords((current) => [record, ...current]);
    return record;
  }, []);

  const saveReview = useCallback(async (id: string, review: ClinicianReview) => {
    setError(null);
    const updated = await apiClient.saveReview(id, review);
    if (updated) {
      setRecords((current) => current.map((record) => (record.id === id ? updated : record)));
    }
    return updated;
  }, []);

  const summary = useMemo<DashboardSummary | null>(() => (isLoading ? null : buildDashboardSummary(records)), [records, isLoading]);

  const value = useMemo(
    () => ({ records, summary, isLoading, error, refresh, createAssessment, saveReview }),
    [records, summary, isLoading, error, refresh, createAssessment, saveReview]
  );

  return <AssessmentsContext.Provider value={value}>{children}</AssessmentsContext.Provider>;
}

export function useAssessmentsStore() {
  const ctx = useContext(AssessmentsContext);
  if (!ctx) throw new Error('useAssessmentsStore must be used within AssessmentsProvider');
  return ctx;
}
