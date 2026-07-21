interface WatchlistButtonProps {
  symbol: string;
  active: boolean;
  onToggle: (symbol: string) => void;
  compact?: boolean;
}

export function WatchlistButton({ symbol, active, onToggle, compact = false }: WatchlistButtonProps) {
  return (
    <button
      type="button"
      className={`watchlist-button${active ? ' is-active' : ''}${compact ? ' is-compact' : ''}`}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onToggle(symbol);
      }}
      aria-pressed={active}
      aria-label={active ? `Remove ${symbol} from watchlist` : `Add ${symbol} to watchlist`}
      title={active ? 'Remove from watchlist' : 'Add to watchlist'}
    >
      <span aria-hidden="true">{active ? '★' : '☆'}</span>
      {!compact ? <span>{active ? 'Watching' : 'Watch'}</span> : null}
    </button>
  );
}
