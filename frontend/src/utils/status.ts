import type { DataStatus } from '../types/data';

export const statusLabel: Record<DataStatus, string> = {
  fresh: 'Fresh',
  cached: 'Cached',
  stale: 'Stale',
  partial: 'Partial',
  unavailable: 'Unavailable',
};

export function scoreBand(score: number | null): 'high' | 'medium' | 'low' | 'missing' {
  if (score === null) return 'missing';
  if (score >= 75) return 'high';
  if (score >= 45) return 'medium';
  return 'low';
}
