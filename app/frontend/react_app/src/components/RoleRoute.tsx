import type { ReactElement } from 'react';
import { Link } from 'react-router-dom';
import { LockKeyhole } from 'lucide-react';
import type { Permission } from '@/lib/permissions';
import { hasPermission } from '@/lib/permissions';
import { useAuth } from '@/context/AuthContext';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/Button';

export function RoleRoute({ permission, children }: { permission: Permission; children: ReactElement }) {
  const { user } = useAuth();

  if (hasPermission(user?.role, permission)) return children;

  return (
    <EmptyState
      title="Restricted workspace"
      description="Your current role does not have access to this clinical operations area. This protects model operations, audit history, and override workflows."
      action={
        <Link to="/command-center">
          <Button variant="secondary">
            <LockKeyhole size={17} /> Back to Command Center
          </Button>
        </Link>
      }
    />
  );
}
