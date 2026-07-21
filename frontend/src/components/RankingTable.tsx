import { Link } from 'react-router-dom';

import type { LatestSymbol } from '../types/data';
import { formatCurrency, formatScore } from '../utils/format';
import { ChangeValue } from './ChangeValue';
import { DataStatusBadge } from './DataStatusBadge';
import { RankChange } from './RankChange';
import { ScoreBadge } from './ScoreBadge';
import { WatchlistButton } from './WatchlistButton';

export type SortKey =
  | 'rank'
  | 'symbol'
  | 'price'
  | 'daily_return_pct'
  | 'hype_score'
  | 'attention_score'
  | 'trading_score'
  | 'confidence_score'
  | 'rank_change';

interface RankingTableProps {
  stocks: LatestSymbol[];
  sortKey: SortKey;
  sortDirection: 'asc' | 'desc';
  onSort: (key: SortKey) => void;
  watchlist: string[];
  onToggleWatchlist: (symbol: string) => void;
}

const columns: Array<{ key: SortKey; label: string; className?: string; title?: string }> = [
  { key: 'rank', label: 'Rank' },
  { key: 'symbol', label: 'Company', className: 'company-column' },
  { key: 'price', label: 'Price' },
  { key: 'daily_return_pct', label: 'Day' },
  { key: 'hype_score', label: 'Hype', title: 'Combined attention and activity score, not a retail ownership percentage.' },
  { key: 'attention_score', label: 'Attention' },
  { key: 'trading_score', label: 'Trading' },
  { key: 'confidence_score', label: 'Confidence' },
  { key: 'rank_change', label: 'Δ Rank' },
];

export function RankingTable({
  stocks,
  sortKey,
  sortDirection,
  onSort,
  watchlist,
  onToggleWatchlist,
}: RankingTableProps) {
  return (
    <div className="table-shell">
      <table className="ranking-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.className} title={column.title}>
                <button type="button" className="sort-button" onClick={() => onSort(column.key)}>
                  {column.label}
                  <span aria-hidden="true" className="sort-indicator">
                    {sortKey === column.key ? (sortDirection === 'asc' ? '↑' : '↓') : '↕'}
                  </span>
                </button>
              </th>
            ))}
            <th>Status</th>
            <th><span className="sr-only">Watchlist</span></th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => (
            <tr key={stock.symbol}>
              <td className="rank-cell"><strong>{stock.rank ?? '—'}</strong></td>
              <td className="company-cell">
                <Link to={`/stock/${stock.symbol}`} className="company-link">
                  <span className="ticker-chip">{stock.symbol}</span>
                  <span>
                    <strong>{stock.company_name}</strong>
                    <small>{stock.sector}</small>
                  </span>
                </Link>
              </td>
              <td className="numeric-cell">{formatCurrency(stock.price)}</td>
              <td className="numeric-cell"><ChangeValue value={stock.daily_return_pct} /></td>
              <td><ScoreBadge value={stock.hype_score} size="small" /></td>
              <td className="numeric-cell score-number">{formatScore(stock.attention_score)}</td>
              <td className="numeric-cell score-number">{formatScore(stock.trading_score)}</td>
              <td className="numeric-cell confidence-cell">
                <span>{formatScore(stock.confidence_score)}</span>
                <span className="mini-progress" aria-hidden="true">
                  <span style={{ width: `${stock.confidence_score}%` }} />
                </span>
              </td>
              <td><RankChange value={stock.rank_change} /></td>
              <td><DataStatusBadge status={stock.data_status} /></td>
              <td>
                <WatchlistButton
                  symbol={stock.symbol}
                  active={watchlist.includes(stock.symbol)}
                  onToggle={onToggleWatchlist}
                  compact
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
