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
  | 'volume_ratio_30d'
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

const columns: Array<{
  key: SortKey;
  label: string;
  className?: string;
  title?: string;
}> = [
  { key: 'rank', label: 'Rank' },
  {
    key: 'symbol',
    label: 'Company',
    className: 'company-column',
  },
  {
    key: 'price',
    label: 'Price',
    title: 'Latest available market price in US dollars.',
  },
  {
    key: 'daily_return_pct',
    label: 'Day',
    title: 'Percentage price change on the latest trading day.',
  },
  {
    key: 'volume_ratio_30d',
    label: 'Vol. vs. 30D',
    title:
      'Latest trading volume divided by the stock’s rolling 30-day median volume. For example, 1.50× means 50% above the recent normal level.',
  },
  {
    key: 'hype_score',
    label: 'Hype',
    title:
      'Combined attention and activity score from 0 to 100. It is not a retail ownership percentage.',
  },
  {
    key: 'attention_score',
    label: 'Attention',
    title:
      'Relative attention score from 0 to 100 based on available public attention signals.',
  },
  {
    key: 'trading_score',
    label: 'Trading Activity',
    title:
      'Relative activity score from 0 to 100 based on unusual volume, absolute price movement and volatility. It is not a price or absolute volume.',
  },
  {
    key: 'confidence_score',
    label: 'Confidence',
    title:
      'Data coverage and freshness score. A higher value means that more required sources and observations were available.',
  },
  {
    key: 'rank_change',
    label: 'Δ Rank',
    title: 'Change compared with the previous available ranking.',
  },
];

function formatVolumeRatio(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return '—';
  }

  return `${value.toFixed(2)}×`;
}

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
              <th
                key={column.key}
                className={column.className}
                title={column.title}
              >
                <button
                  type="button"
                  className="sort-button"
                  onClick={() => onSort(column.key)}
                >
                  {column.label}

                  <span aria-hidden="true" className="sort-indicator">
                    {sortKey === column.key
                      ? sortDirection === 'asc'
                        ? '↑'
                        : '↓'
                      : '↕'}
                  </span>
                </button>
              </th>
            ))}

            <th>Status</th>

            <th>
              <span className="sr-only">Watchlist</span>
            </th>
          </tr>
        </thead>

        <tbody>
          {stocks.map((stock) => (
            <tr key={stock.symbol}>
              <td className="rank-cell">
                <strong>{stock.rank ?? '—'}</strong>
              </td>

              <td className="company-cell">
                <Link
                  to={`/stock/${stock.symbol}`}
                  className="company-link"
                >
                  <span className="ticker-chip">
                    {stock.symbol}
                  </span>

                  <span>
                    <strong>{stock.company_name}</strong>
                    <small>{stock.sector}</small>
                  </span>
                </Link>
              </td>

              <td className="numeric-cell">
                {formatCurrency(stock.price)}
              </td>

              <td className="numeric-cell">
                <ChangeValue value={stock.daily_return_pct} />
              </td>

              <td
                className="numeric-cell"
                title={
                  stock.volume_ratio_30d === null
                    ? '30-day volume comparison unavailable'
                    : `Current volume is ${stock.volume_ratio_30d.toFixed(
                        2,
                      )} times the rolling 30-day median.`
                }
              >
                {formatVolumeRatio(stock.volume_ratio_30d)}
              </td>

              <td>
                <ScoreBadge
                  value={stock.hype_score}
                  size="small"
                />
              </td>

              <td className="numeric-cell score-number">
                {formatScore(stock.attention_score)}
              </td>

              <td
                className="numeric-cell score-number"
                title="Trading Activity Score from 0 to 100"
              >
                {stock.trading_score === null
                  ? '—'
                  : `${formatScore(stock.trading_score)} / 100`}
              </td>

              <td className="numeric-cell confidence-cell">
                <span>
                  {formatScore(stock.confidence_score)}
                </span>

                <span
                  className="mini-progress"
                  aria-hidden="true"
                >
                  <span
                    style={{
                      width: `${stock.confidence_score}%`,
                    }}
                  />
                </span>
              </td>

              <td>
                <RankChange value={stock.rank_change} />
              </td>

              <td>
                <DataStatusBadge status={stock.data_status} />
              </td>

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