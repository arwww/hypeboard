import { formatScore } from '../utils/format';
import { scoreBand } from '../utils/status';

interface ScoreBadgeProps {
  value: number | null;
  label?: string;
  size?: 'small' | 'medium' | 'large';
  showCoverage?: number;
}

export function ScoreBadge({ value, label, size = 'medium', showCoverage }: ScoreBadgeProps) {
  const band = scoreBand(value);
  return (
    <div className={`score-badge score-${band} score-${size}`} aria-label={`${label ?? 'Score'}: ${formatScore(value)}`}>
      <span className="score-value">{formatScore(value)}</span>
      {label ? <span className="score-label">{label}</span> : null}
      {showCoverage !== undefined ? (
        <span className="score-coverage">{Math.round(showCoverage * 100)}% coverage</span>
      ) : null}
    </div>
  );
}
