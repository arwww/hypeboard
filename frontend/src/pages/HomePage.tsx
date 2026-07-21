import { useMemo, useState } from 'react';

import { DisclaimerBanner } from '../components/DisclaimerBanner';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { InsightCard } from '../components/InsightCard';
import { LoadingState } from '../components/LoadingState';
import { MetricCard } from '../components/MetricCard';
import { RankingControls } from '../components/RankingControls';
import { RankingTable, type SortKey } from '../components/RankingTable';
import { SourceStatusStrip } from '../components/SourceStatusStrip';
import { StockCard } from '../components/StockCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { useLocalStorage } from '../hooks/useLocalStorage';
import type { LatestSymbol } from '../types/data';
import { formatDate, formatDateTime } from '../utils/format';

function comparableValue(stock: LatestSymbol, key: SortKey): number | string | null {
  if (key === 'symbol') return stock.symbol;
  return stock[key];
}

function sortStocks(stocks: LatestSymbol[], key: SortKey, direction: 'asc' | 'desc') {
  return [...stocks].sort((left, right) => {
    const a = comparableValue(left, key);
    const b = comparableValue(right, key);
    if (a === null && b === null) return 0;
    if (a === null) return 1;
    if (b === null) return -1;
    const comparison = typeof a === 'string'
      ? a.localeCompare(String(b))
      : Number(a) - Number(b);
    return direction === 'asc' ? comparison : -comparison;
  });
}

export function HomePage() {
  const { data, loading, error } = useDashboardData();
  const [query, setQuery] = useState('');
  const [sector, setSector] = useState('all');
  const [minimumConfidence, setMinimumConfidence] = useState(0);
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [viewMode, setViewMode] = useLocalStorage<'table' | 'cards'>('hypeboard-view-mode', 'table');
  const [watchlist, setWatchlist] = useLocalStorage<string[]>('hypeboard-watchlist', []);
  const [sortKey, setSortKey] = useState<SortKey>('rank');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const toggleWatchlist = (symbol: string) => {
    setWatchlist((current) => current.includes(symbol)
      ? current.filter((item) => item !== symbol)
      : [...current, symbol]);
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((current) => current === 'asc' ? 'desc' : 'asc');
      return;
    }
    setSortKey(key);
    setSortDirection(key === 'rank' || key === 'symbol' ? 'asc' : 'desc');
  };

  const sectors = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.latest.symbols.map((stock) => stock.sector))].sort();
  }, [data]);

  const filteredStocks = useMemo(() => {
    if (!data) return [];
    const normalizedQuery = query.trim().toLowerCase();
    const filtered = data.latest.symbols.filter((stock) => {
      const matchesText = !normalizedQuery
        || stock.symbol.toLowerCase().includes(normalizedQuery)
        || stock.company_name.toLowerCase().includes(normalizedQuery);
      return matchesText
        && (sector === 'all' || stock.sector === sector)
        && stock.confidence_score >= minimumConfidence
        && (!watchlistOnly || watchlist.includes(stock.symbol));
    });
    return sortStocks(filtered, sortKey, sortDirection);
  }, [data, minimumConfidence, query, sector, sortDirection, sortKey, watchlist, watchlistOnly]);

  if (loading) return <div className="container page-space"><LoadingState /></div>;
  if (error || !data) return <div className="container page-space"><ErrorState message={error ?? 'No data returned'} /></div>;

  const ranked = data.latest.symbols.filter((stock) => stock.rank !== null);
  const biggestScoreRiser = [...ranked]
    .filter((stock) => stock.hype_score_change !== null)
    .sort((a, b) => (b.hype_score_change ?? -Infinity) - (a.hype_score_change ?? -Infinity))[0];
  const highestAttention = [...ranked]
    .filter((stock) => stock.attention_score !== null)
    .sort((a, b) => (b.attention_score ?? -Infinity) - (a.attention_score ?? -Infinity))[0];
  const unusualVolume = [...ranked]
    .filter((stock) => stock.volume_ratio_30d !== null)
    .sort((a, b) => (b.volume_ratio_30d ?? -Infinity) - (a.volume_ratio_30d ?? -Infinity))[0];
  const topHype = [...ranked].sort((a, b) => (b.hype_score ?? -Infinity) - (a.hype_score ?? -Infinity))[0];

  return (
    <>
      <section className="hero-section">
        <div className="hero-orb hero-orb-one" />
        <div className="hero-orb hero-orb-two" />
        <div className="container hero-content">
          <div className="hero-copy">
            <span className="eyebrow"><span className="live-dot" /> Daily public-signal monitor</span>
            <h1>See where market attention is concentrating.</h1>
            <p className="hero-subtitle">Public signals of market attention and retail activity</p>
            <p className="hero-description">
              Hypeboard combines public attention, trading activity, retail-oriented proxies and market-impact signals into a transparent relative ranking.
            </p>
          </div>
          <div className="hero-score-card">
            <span>Current #1</span>
            <div>
              <strong>{topHype?.symbol ?? '—'}</strong>
              <em>{topHype?.hype_score === null || topHype === undefined ? '—' : Math.round(topHype.hype_score)}</em>
            </div>
            <p>{topHype?.drivers[0] ?? 'No validated driver is currently available.'}</p>
            <small>Hype Score · relative signal, not retail ownership</small>
          </div>
        </div>
      </section>

      <div className="container dashboard-flow">
        <section className="metric-grid" aria-label="Update summary">
          <MetricCard label="Last update" value={formatDateTime(data.meta.generated_at)} detail="Validated static data build" icon="↻" />
          <MetricCard label="Latest market day" value={formatDate(data.meta.latest_market_date)} detail="No duplicate weekend observations" icon="⌁" />
          <MetricCard label="Observed stocks" value={data.meta.universe_size} detail={`${data.meta.successful_symbols} updated · ${data.meta.failed_symbols} failed`} icon="▦" />
          <MetricCard label="Score model" value={`v${data.meta.score_version}`} detail="Transparent rule-based weights" icon="ƒ" />
        </section>

        <SourceStatusStrip sources={data.meta.sources} />

        <section className="insights-grid" aria-label="Signal highlights">
          <InsightCard eyebrow="Highest Hype Score" stock={topHype} metric="hype_score" detail="Strongest combined public-signal reading in the current universe." />
          <InsightCard eyebrow="Biggest score increase" stock={biggestScoreRiser} metric="hype_score_change" detail="Largest Hype Score increase versus the previous comparable signal observation." />
          <InsightCard eyebrow="Highest attention" stock={highestAttention} metric="attention_score" detail="Strongest measured public-attention shock among covered symbols." />
          {unusualVolume ? (
            <InsightCard eyebrow="Most unusual volume" stock={unusualVolume} metric="volume_ratio_30d" detail="Largest volume multiple versus its rolling 30-day reference." />
          ) : (
            <article className="insight-card insight-unavailable">
              <span className="insight-eyebrow">Most unusual volume</span>
              <div className="insight-main"><strong>Pending</strong><span>—</span></div>
              <p>A 30-day market history is required before the volume ratio is published.</p>
              <small>No replacement value was invented.</small>
            </article>
          )}
        </section>

        <section className="ranking-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Observed universe</span>
              <h2>Hype ranking</h2>
              <p>Scores compare each stock with its own recent history and, where applicable, the current universe.</p>
            </div>
            <div className="result-count">{filteredStocks.length} of {data.latest.symbols.length}</div>
          </div>

          <RankingControls
            query={query}
            onQueryChange={setQuery}
            sector={sector}
            onSectorChange={setSector}
            sectors={sectors}
            minimumConfidence={minimumConfidence}
            onMinimumConfidenceChange={setMinimumConfidence}
            watchlistOnly={watchlistOnly}
            onWatchlistOnlyChange={setWatchlistOnly}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          />

          {filteredStocks.length === 0 ? (
            <EmptyState title="No stocks match these filters" detail="Clear the search, lower the confidence threshold or add symbols to the local watchlist." />
          ) : viewMode === 'table' ? (
            <RankingTable
              stocks={filteredStocks}
              sortKey={sortKey}
              sortDirection={sortDirection}
              onSort={handleSort}
              watchlist={watchlist}
              onToggleWatchlist={toggleWatchlist}
            />
          ) : (
            <div className="stock-card-grid">
              {filteredStocks.map((stock) => (
                <StockCard
                  key={stock.symbol}
                  stock={stock}
                  watching={watchlist.includes(stock.symbol)}
                  onToggleWatchlist={toggleWatchlist}
                />
              ))}
            </div>
          )}
        </section>

        {data.meta.warnings.length > 0 ? (
          <section className="warning-panel">
            <div><span aria-hidden="true">!</span><strong>Current data notes</strong></div>
            <ul>{data.meta.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
          </section>
        ) : null}

        <DisclaimerBanner notice={data.meta.legal_notice} />
      </div>
    </>
  );
}
