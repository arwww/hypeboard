import { formatPercent } from '../utils/format';

export function ChangeValue({ value }: { value: number | null }) {
  const direction = value === null || value === 0 ? 'flat' : value > 0 ? 'positive' : 'negative';
  return <span className={`change-value change-${direction}`}>{formatPercent(value)}</span>;
}
