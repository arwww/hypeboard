import { Link } from 'react-router-dom';
import type { LatestSymbol } from '../types/data';
import { formatCompact, formatScore } from '../utils/format';

interface InsightCardProps {
  eyebrow: string;
  stock: LatestSymbol | undefined;
  metric: 'hype_score' | 'hype_score_change' | 'attention_score' | 'volume_ratio_30d' | 'rank_change';
  detail: string;
}

export function InsightCard({ eyebrow, stock, metric, detail }: InsightCardProps) {
  if (!stock) return null;
  const rawValue = stock[metric];
  const value = metric === 'volume_ratio_30d'
    ? (rawValue === null ? '—' : `${Number(rawValue).toFixed(1)}×`)
    : metric === 'rank_change' || metric === 'hype_score_change'
      ? (rawValue === null ? '—' : `${Number(rawValue) > 0 ? '+' : ''}${Number(rawValue).toFixed(metric === 'hype_score_change' ? 1 : 0)}`)
      : formatScore(rawValue);
  return (
    <Link to={`/stock/${stock.symbol}`} className="insight-card">
      <span className="insight-eyebrow">{eyebrow}</span>
      <div className="insight-main">
        <strong>{stock.symbol}</strong>
        <span>{value}</span>
      </div>
      <p>{detail}</p>
      <small>{stock.company_name} · {stock.volume ? `${formatCompact(stock.volume)} shares` : 'volume unavailable'}</small>
    </Link>
  );
}
