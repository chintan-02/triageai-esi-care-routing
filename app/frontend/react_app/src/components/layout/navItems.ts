import { ClipboardList, FileText, Gauge, LayoutDashboard, Settings, ShieldCheck, Stethoscope, type LucideIcon } from 'lucide-react';
import type { Permission } from '@/lib/permissions';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  permission?: Permission;
}

export const navItems: NavItem[] = [
  { to: '/command-center', label: 'Command Center', icon: LayoutDashboard },
  { to: '/new-assessment', label: 'New Intake', icon: Stethoscope, permission: 'assessment:create' },
  { to: '/assessments', label: 'Assessments', icon: ClipboardList, permission: 'assessment:read' },
  { to: '/reports', label: 'Reports', icon: FileText, permission: 'report:generate' },
  { to: '/audit', label: 'Audit Trail', icon: ShieldCheck, permission: 'audit:read' },
  { to: '/model-monitoring', label: 'Model Monitoring', icon: Gauge, permission: 'model:read' },
  { to: '/settings', label: 'Settings', icon: Settings, permission: 'settings:read' }
];
