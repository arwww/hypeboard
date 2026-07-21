import { Link, useParams } from 'react-router-dom';

import { ChangeValue } from '../components/ChangeValue';
import { DataStatusBadge } from '../components/DataStatusBadge';
import { DisclaimerBanner } from '../components/DisclaimerBanner';
import { DriverList } from '../components/DriverList';
import { ErrorState } from '../components/ErrorState';
import { HistoryChart } from '../components/HistoryChart';
import { LoadingState } from '../components/LoadingState';
import { ScoreBadge } from '../components/ScoreBadge';
import { ScoreComposition } from '../components/ScoreComposition';
import { SourceTable } from '../components/SourceTable';
import { WatchlistButton } from '../components/WatchlistButton';
import { useDashboardData } from '../hooks/useDashboardData';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useSymbolHistory } from '../hooks/useSymbolHistory';
import { formatCompact, formatCurrency, formatDate, formatScore } from '../utils/format';

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const dashboard = useDashboardData();
  const history = useSymbolHistory(symbol);
  const [watchlist, setWatchlist] = useLocalStorage<string[]>('hypeboard-watchlist', []);

  const toggleWatchlist = (ticker: string) => {
    setWatchlist((current) => current.includes(ticker)
      ? current.filter((item) => item !== ticker)
      : [...current, ticker]);
  };

  if (dashboard.loading || history.loading) return <div className="container page-space"><LoadingState label={`Loading ${symbol ?? ''} analysis…`} /></div>;
  if (dashboard.error || history.error || !dashboard.data || !history.data) {
    return <div className="container page-space"><ErrorState message={dashboard.error ?? history.error ?? 'Stock data unavailable'} /></div>;
  }

  const ticker = symbol?.toUpperCase() ?? '';
  const stock = dashboard.data.latest.symbols.find((item) => item.symbol === ticker);
  if (!stock) {
    return (
      <div className="container page-space">
        <div className="state-panel state-error">
          <h2>Symbol not found</h2>
          <p>{ticker || 'This symbol'} is not part of the active Hypeboard universe.</p>
          <Link className="primary-button" to="/">Back to dashboard</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container detail-page page-space">
      <div className="breadcrumb"><Link to="/">Dashboard</Link><span>/</span><span>{stock.symbol}</span></div>

      <section className="detail-hero">
        <div className="detail-identity">
          <div className="detail-symbol-row">
            <span className="ticker-large">{stock.symbol}</span>
            <DataStatusBadge status={stock.data_status} />
          </div>
          <h1>{stock.company_name}</h1>
          <p>{stock.exchange} · {stock.sector} · Market data through {formatDate(stock.source_dates.market ?? null)}</p>
          <WatchlistButton
            symbol={stock.symbol}
            active={watchlist.includes(stock.symbol)}
            onToggle={toggleWatchlist}
          />
        </div>
        <div className="detail-price">
          <span>Last close</span>
          <strong>{formatCurrency(stock.price)}</strong>
          <ChangeValue value={stock.daily_return_pct} />
        </div>
        <div className="detail-rank">
          <span>Current rank</span>
          <strong>#{stock.rank ?? '—'}</strong>
          <small>{stock.rank_change === null ? 'No comparable prior rank' : `${stock.rank_change > 0 ? '+' : ''}${stock.rank_change} places`} · {stock.hype_score_change === null ? 'score change unavailable' : `${stock.hype_score_change > 0 ? '+' : ''}${stock.hype_score_change.toFixed(1)} score`}</small>
        </div>
        <ScoreBadge value={stock.hype_score} label="Hype Score" size="large" showCoverage={stock.score_coverage} />
        <ScoreBadge value={stock.confidence_score} label="Confidence" size="large" />
      </section>

      <section className="detail-grid detail-summary-grid">
        <article className="panel score-panel">
          <div className="panel-heading">
            <div><span className="section-kicker">Score anatomy</span><h2>Component signals</h2></div>
            <span className="formula-note">40 / 35 / 15 / 10</span>
          </div>
          <ScoreComposition stock={stock} />
          <p className="panel-footnote">Weights: Attention 40%, Trading Activity 35%, Retail Proxy 15%, Market Impact 10%. Missing components are only renormalized above configured minimum coverage.</p>
        </article>

        <article className="panel drivers-panel">
          <div className="panel-heading"><div><span className="section-kicker">Explainability</span><h2>Validated drivers</h2></div></div>
          <DriverList drivers={stock.drivers} />
        </article>
      </section>

      <section className="detail-stats-grid">
        <article><span>Attention</span><strong>{formatScore(stock.attention_score)}</strong><small>Public interest shock</small></article>
        <article><span>Trading activity</span><strong>{formatScore(stock.trading_score)}</strong><small>Volume, move, volatility</small></article>
        <article><span>Retail proxy</span><strong>{formatScore(stock.retail_proxy_score)}</strong><small>Proxy, not broker share</small></article>
        <article><span>Market impact</span><strong>{formatScore(stock.impact_score)}</strong><small>Sensitivity to activity</small></article>
        <article><span>Volume</span><strong>{formatCompact(stock.volume)}</strong><small>{stock.volume_ratio_30d === null ? '30-day ratio unavailable' : `${stock.volume_ratio_30d.toFixed(2)}× 30-day normal`}</small></article>
      </section>

      <section className="chart-grid">
        <article className="panel chart-panel">
          <div className="panel-heading"><div><span className="section-kicker">History</span><h2>Hype Score</h2></div></div>
          <HistoryChart points={history.data.points} metric="hype_score" title={`${stock.symbol} historical Hype Score`} />
        </article>
        <article className="panel chart-panel">
          <div className="panel-heading"><div><span className="section-kicker">Attention</span><h2>Public attention signal</h2></div></div>
          <HistoryChart points={history.data.points} metric="attention_score" title={`${stock.symbol} historical attention score`} />
        </article>
        <article className="panel chart-panel chart-wide">
          <div className="panel-heading"><div><span className="section-kicker">Activity</span><h2>Volume versus normal</h2></div></div>
          {history.data.points.some((point) => point.volume_ratio_30d !== null) ? (
            <HistoryChart points={history.data.points} metric="volume_ratio_30d" title={`${stock.symbol} volume ratio versus 30-day baseline`} />
          ) : (
            <div className="chart-no-data">
              <strong>Not enough market history yet</strong>
              <p>The pipeline will publish this chart after the minimum rolling window is available. Missing history is not replaced with zero.</p>
            </div>
          )}
        </article>
      </section>

      <section className="panel source-detail-panel">
        <div className="panel-heading"><div><span className="section-kicker">Provenance</span><h2>Sources and freshness</h2></div></div>
        <SourceTable sources={history.data.sources} />
      </section>

      <section className="panel limitations-panel">
        <div className="panel-heading"><div><span className="section-kicker">Method limits</span><h2>What to keep in mind</h2></div></div>
        <ul>{history.data.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
        <Link to="/methodology" className="text-link">Read the full methodology →</Link>
      </section>

      <DisclaimerBanner notice={dashboard.data.meta.legal_notice} />
    </div>
  );
}
