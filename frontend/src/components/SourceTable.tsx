import type { SourceRunStatus } from '../types/data';
import { formatDate, formatDateTime } from '../utils/format';
import { DataStatusBadge } from './DataStatusBadge';

const sourceLabels: Record<string, string> = {
  market_data: 'Market data',
  wikipedia: 'Wikimedia Pageviews',
  finra_short_volume: 'FINRA short-sale volume',
  social: 'Social attention feed',
};

export function SourceTable({ sources }: { sources: SourceRunStatus[] }) {
  return (
    <div className="source-table-shell">
      <table className="source-table">
        <thead>
          <tr><th>Source</th><th>Status</th><th>Observation</th><th>Retrieved</th><th>Coverage</th><th>Delay / limitation</th></tr>
        </thead>
        <tbody>
          {sources.map((source) => (
            <tr key={source.source}>
              <td><strong>{sourceLabels[source.source] ?? source.source}</strong></td>
              <td><DataStatusBadge status={source.status} /></td>
              <td>{formatDate(source.last_observation_at)}</td>
              <td>{formatDateTime(source.retrieved_at)}</td>
              <td>{source.symbols_updated} symbols</td>
              <td>{source.error ? `${source.error}. ` : ''}{source.delay_note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
