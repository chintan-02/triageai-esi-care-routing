import { render, screen } from '@testing-library/react';
import { MemoryRouter, Outlet, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

const mockUseAuth = vi.fn();

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => mockUseAuth()
}));

vi.mock('@/components/ProtectedRoute', () => ({
  ProtectedRoute: () => <Outlet />
}));

vi.mock('@/components/layout/AppShell', () => ({
  AppShell: () => <><Outlet /><div>AppShell</div></>
}));

vi.mock('@/components/RoleRoute', () => ({
  RoleRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

vi.mock('@/context/AssessmentsContext', () => ({
  AssessmentsProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

vi.mock('@/context/ModelStatusContext', () => ({
  ModelStatusProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>
}));

vi.mock('@/components/ui/Skeleton', () => ({
  SkeletonStatRow: () => <div>Loading</div>
}));

vi.mock('@/features/auth/pages/LoginPage', () => ({
  LoginPage: () => <div>Login Page</div>
}));

vi.mock('@/features/dashboard/pages/DashboardPage', () => ({
  DashboardPage: () => <div>Dashboard Page</div>
}));

vi.mock('@/features/assessments/pages/AssessmentsPage', () => ({
  AssessmentsPage: () => <div>Assessments Page</div>
}));

vi.mock('@/features/assessments/pages/NewAssessmentPage', () => ({
  NewAssessmentPage: () => <div>New Assessment Page</div>
}));

vi.mock('@/features/assessments/pages/AssessmentDetailPage', () => ({
  AssessmentDetailPage: () => <div>Assessment Detail Page</div>
}));

vi.mock('@/features/reports/pages/ReportsPage', () => ({
  ReportsPage: () => <div>Reports Page</div>
}));

vi.mock('@/features/audit/pages/AuditPage', () => ({
  AuditPage: () => <div>Audit Page</div>
}));

vi.mock('@/features/model/pages/ModelMonitoringPage', () => ({
  ModelMonitoringPage: () => <div>Model Monitoring Page</div>
}));

vi.mock('@/features/model/pages/SettingsPage', () => ({
  SettingsPage: () => <div>Settings Page</div>
}));

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

describe('App routing auth flow', () => {
  beforeEach(() => {
    mockUseAuth.mockReset();
  });

  it('redirects unauthenticated users to the login route', async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn()
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <LocationProbe />
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByText('Login Page')).toBeInTheDocument();
    expect(screen.getByTestId('location').textContent).toBe('/login');
  });

  it('redirects authenticated users to the command center route', async () => {
    mockUseAuth.mockReturnValue({
      user: { name: 'Dr. Rivera', role: 'Doctor', initials: 'DR' },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn()
    });

    render(
      <MemoryRouter initialEntries={['/']}>
        <LocationProbe />
        <App />
      </MemoryRouter>
    );

    expect(await screen.findByText('Dashboard Page')).toBeInTheDocument();
    expect(screen.getByTestId('location').textContent).toBe('/command-center');
  });
});
