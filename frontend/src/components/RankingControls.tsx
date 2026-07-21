interface RankingControlsProps {
  query: string;
  onQueryChange: (value: string) => void;
  sector: string;
  onSectorChange: (value: string) => void;
  sectors: string[];
  minimumConfidence: number;
  onMinimumConfidenceChange: (value: number) => void;
  watchlistOnly: boolean;
  onWatchlistOnlyChange: (value: boolean) => void;
  viewMode: 'table' | 'cards';
  onViewModeChange: (value: 'table' | 'cards') => void;
}

export function RankingControls({
  query,
  onQueryChange,
  sector,
  onSectorChange,
  sectors,
  minimumConfidence,
  onMinimumConfidenceChange,
  watchlistOnly,
  onWatchlistOnlyChange,
  viewMode,
  onViewModeChange,
}: RankingControlsProps) {
  return (
    <div className="ranking-controls">
      <label className="search-field">
        <span className="sr-only">Search symbols or companies</span>
        <span aria-hidden="true">⌕</span>
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search ticker or company"
        />
      </label>
      <label className="select-field">
        <span>Sector</span>
        <select value={sector} onChange={(event) => onSectorChange(event.target.value)}>
          <option value="all">All sectors</option>
          {sectors.map((value) => <option key={value} value={value}>{value}</option>)}
        </select>
      </label>
      <label className="select-field confidence-filter">
        <span>Min. confidence</span>
        <select
          value={minimumConfidence}
          onChange={(event) => onMinimumConfidenceChange(Number(event.target.value))}
        >
          {[0, 40, 60, 75, 90].map((value) => <option key={value} value={value}>{value === 0 ? 'Any' : `${value}+`}</option>)}
        </select>
      </label>
      <label className="toggle-control">
        <input
          type="checkbox"
          checked={watchlistOnly}
          onChange={(event) => onWatchlistOnlyChange(event.target.checked)}
        />
        <span className="toggle-track" aria-hidden="true"><span /></span>
        <span>Watchlist only</span>
      </label>
      <div className="segmented-control" aria-label="View mode">
        <button
          type="button"
          className={viewMode === 'table' ? 'active' : ''}
          onClick={() => onViewModeChange('table')}
          aria-pressed={viewMode === 'table'}
        >
          Table
        </button>
        <button
          type="button"
          className={viewMode === 'cards' ? 'active' : ''}
          onClick={() => onViewModeChange('cards')}
          aria-pressed={viewMode === 'cards'}
        >
          Cards
        </button>
      </div>
    </div>
  );
}
