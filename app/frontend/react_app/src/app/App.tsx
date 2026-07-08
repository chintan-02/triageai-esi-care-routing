import { lazy, Suspense } from 'react';
import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { RoleRoute } from '@/components/RoleRoute';
import { AssessmentsProvider } from '@/context/AssessmentsContext';
import { ModelStatusProvider } from '@/context/ModelStatusContext';
import { SkeletonStatRow } from '@/components/ui/Skeleton';
import { useAuth } from '@/context/AuthContext';

const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage').then((module) => ({ default: module.LoginPage })));
const DashboardPage = lazy(() => import('@/features/dashboard/pages/DashboardPage').then((module) => ({ default: module.DashboardPage })));
const AssessmentsPage = lazy(() => import('@/features/assessments/pages/AssessmentsPage').then((module) => ({ default: module.AssessmentsPage })));
const NewAssessmentPage = lazy(() => import('@/features/assessments/pages/NewAssessmentPage').then((module) => ({ default: module.NewAssessmentPage })));
const AssessmentDetailPage = lazy(() => import('@/features/assessments/pages/AssessmentDetailPage').then((module) => ({ default: module.AssessmentDetailPage })));
const ReportsPage = lazy(() => import('@/features/reports/pages/ReportsPage').then((module) => ({ default: module.ReportsPage })));
const AuditPage = lazy(() => import('@/features/audit/pages/AuditPage').then((module) => ({ default: module.AuditPage })));
const ModelMonitoringPage = lazy(() => import('@/features/model/pages/ModelMonitoringPage').then((module) => ({ default: module.ModelMonitoringPage })));
const SettingsPage = lazy(() => import('@/features/model/pages/SettingsPage').then((module) => ({ default: module.SettingsPage })));

function DataScope() {
  return (
    <ModelStatusProvider>
      <AssessmentsProvider>
        <Outlet />
      </AssessmentsProvider>
    </ModelStatusProvider>
  );
}

function RouteFallback() {
  return (
    <div className="p-6">
      <SkeletonStatRow />
    </div>
  );
}

function RootRedirect() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <RouteFallback />;
  return user ? <Navigate to="/command-center" replace /> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DataScope />}>
            <Route element={<AppShell />}>
              <Route path="/command-center" element={<DashboardPage />} />
              <Route path="assessments" element={<AssessmentsPage />} />
              <Route path="assessments/:id" element={<AssessmentDetailPage />} />
              <Route path="new-assessment" element={<RoleRoute permission="assessment:create"><NewAssessmentPage /></RoleRoute>} />
              <Route path="model-monitoring" element={<RoleRoute permission="model:read"><ModelMonitoringPage /></RoleRoute>} />
              <Route path="reports" element={<RoleRoute permission="report:generate"><ReportsPage /></RoleRoute>} />
              <Route path="audit" element={<RoleRoute permission="audit:read"><AuditPage /></RoleRoute>} />
              <Route path="settings" element={<RoleRoute permission="settings:read"><SettingsPage /></RoleRoute>} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
