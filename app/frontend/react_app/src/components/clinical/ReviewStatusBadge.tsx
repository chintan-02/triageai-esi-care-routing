import type { ReviewStatus } from '@/types/clinical';
import { Badge } from '@/components/ui/Badge';

const tones: Record<ReviewStatus, string> = {
  pending: 'border-amber-200 bg-amber-50 text-amber-800',
  accepted: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  overridden: 'border-blue-200 bg-blue-50 text-blue-800'
};

const labels: Record<ReviewStatus, string> = {
  pending: 'Pending review',
  accepted: 'Accepted',
  overridden: 'Overridden'
};

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  return <Badge className={tones[status]}>{labels[status]}</Badge>;
}
