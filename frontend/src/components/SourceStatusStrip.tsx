import type { SourceRunStatus } from '../types/data';
import { formatDate } from '../utils/format';
import { DataStatusBadge } from './DataStatusBadge';

const sourceNames: Record<string, string> = {
  market_data: 'Market data',
  wikipedia: 'Wikipedia',
  finra_short_volume: 'FINRA short volume',
  social: 'Social',
};

export function SourceStatusStrip({ sources }: { sources: SourceRunStatus[] }) {
  return (
    <section className="source-strip" aria-label="Data source status">
      {sources.map((source) => (
        <div className="source-pill" key={source.source} title={source.error ?? source.delay_note}>
          <div>
            <strong>{sourceNames[source.source] ?? source.source}</strong>
            <span>{formatDate(source.last_observation_at)}</span>
          </div>
          <DataStatusBadge status={source.status} />
        </div>
      ))}
    </section>
  );
}
