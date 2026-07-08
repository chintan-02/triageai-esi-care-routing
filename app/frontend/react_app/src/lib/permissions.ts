import type { ClinicianRole } from '@/types/auth';

export type Permission =
  | 'assessment:create'
  | 'assessment:read'
  | 'review:accept'
  | 'review:override'
  | 'report:generate'
  | 'audit:read'
  | 'model:read'
  | 'settings:read';

const rolePermissions: Record<ClinicianRole, Permission[]> = {
  Nurse: ['assessment:create', 'assessment:read', 'review:accept', 'report:generate'],
  Doctor: ['assessment:create', 'assessment:read', 'review:accept', 'review:override', 'report:generate', 'audit:read'],
  Admin: ['assessment:read', 'report:generate', 'audit:read', 'model:read', 'settings:read']
};

export function hasPermission(role: ClinicianRole | undefined, permission: Permission) {
  if (!role) return false;
  return rolePermissions[role].includes(permission);
}

export function roleSummary(role: ClinicianRole) {
  switch (role) {
    case 'Nurse':
      return 'Create assessments, accept final decisions, and generate reports.';
    case 'Doctor':
      return 'Review high-risk cases, accept or override final ESI decisions, and inspect audit history.';
    case 'Admin':
      return 'Monitor model operations, settings, audit trail, and reporting access.';
    default:
      return '';
  }
}
