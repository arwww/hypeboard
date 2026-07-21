import type { DataStatus } from '../types/data';
import { statusLabel } from '../utils/status';

export function DataStatusBadge({ status }: { status: DataStatus }) {
  return <span className={`status-badge status-${status}`}>{statusLabel[status]}</span>;
}
