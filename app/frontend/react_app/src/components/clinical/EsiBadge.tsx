import type { EsiLevel } from '@/types/clinical';
import { esiLabel, esiSolidTone } from '@/lib/formatters';
import { Badge } from '@/components/ui/Badge';

export function EsiBadge({ level, prefix }: { level: EsiLevel; prefix?: string }) {
  return (
    <Badge className={esiSolidTone(level)}>
      {prefix ? `${prefix}: ` : ''}
      {esiLabel(level)}
    </Badge>
  );
}
