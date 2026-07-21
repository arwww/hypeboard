import { Link } from 'react-router-dom';

import type { LatestSymbol } from '../types/data';
import { formatCurrency, formatScore } from '../utils/format';
import { ChangeValue } from './ChangeValue';
import { DataStatusBadge } from './DataStatusBadge';
import { RankChange } from './RankChange';
import { ScoreBadge } from './ScoreBadge';
import { WatchlistButton } from './WatchlistButton';

interface StockCardProps {
  stock: LatestSymbol;
  watching: boolean;
  onToggleWatchlist: (symbol: string) => void;
}

export function StockCard({ stock, watching, onToggleWatchlist }: StockCardProps) {
  return (
    <article className="stock-card">
      <div className="stock-card-header">
        <Link to={`/stock/${stock.symbol}`} className="stock-card-title">
          <span className="stock-rank">#{stock.rank ?? '—'}</span>
          <div>
            <strong>{stock.symbol}</strong>
            <span>{stock.company_name}</span>
          </div>
        </Link>
        <WatchlistButton symbol={stock.symbol} active={watching} onToggle={onToggleWatchlist} compact />
      </div>
      <div className="stock-card-core">
        <ScoreBadge value={stock.hype_score} label="Hype" size="large" showCoverage={stock.score_coverage} />
        <div className="stock-price-block">
          <strong>{formatCurrency(stock.price)}</strong>
          <ChangeValue value={stock.daily_return_pct} />
          <DataStatusBadge status={stock.data_status} />
        </div>
      </div>
      <dl className="stock-card-scores">
        <div><dt>Attention</dt><dd>{formatScore(stock.attention_score)}</dd></div>
        <div><dt>Trading</dt><dd>{formatScore(stock.trading_score)}</dd></div>
        <div><dt>Retail proxy</dt><dd>{formatScore(stock.retail_proxy_score)}</dd></div>
        <div><dt>Confidence</dt><dd>{formatScore(stock.confidence_score)}</dd></div>
      </dl>
      <div className="stock-card-footer">
        <RankChange value={stock.rank_change} />
        <span>{stock.sector}</span>
        <Link to={`/stock/${stock.symbol}`}>Open analysis →</Link>
      </div>
    </article>
  );
}
