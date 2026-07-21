export function RankChange({ value }: { value: number | null }) {
  if (value === null) return <span className="rank-change rank-flat">—</span>;
  if (value === 0) return <span className="rank-change rank-flat">0</span>;
  return (
    <span className={`rank-change ${value > 0 ? 'rank-up' : 'rank-down'}`}>
      <span aria-hidden="true">{value > 0 ? '↑' : '↓'}</span> {Math.abs(value)}
    </span>
  );
}
