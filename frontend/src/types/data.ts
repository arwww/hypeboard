export type DataStatus = 'fresh' | 'cached' | 'stale' | 'partial' | 'unavailable';

export interface SourceRunStatus {
  source: string;
  status: DataStatus;
  last_observation_at: string | null;
  retrieved_at: string;
  records: number;
  symbols_updated: number;
  error: string | null;
  delay_note: string;
}

export interface LatestSymbol {
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string;
  price: number | null;
  daily_return_pct: number | null;
  volume: number | null;
  volume_ratio_30d: number | null;
  attention_score: number | null;
  trading_score: number | null;
  retail_proxy_score: number | null;
  impact_score: number | null;
  hype_score: number | null;
  hype_score_change: number | null;
  confidence_score: number;
  rank: number | null;
  rank_change: number | null;
  data_status: DataStatus;
  drivers: string[];
  score_coverage: number;
  source_dates: Record<string, string | null>;
}

export interface LatestPayload {
  generated_at: string;
  market_date: string | null;
  score_version: string;
  symbols: LatestSymbol[];
}

export interface MetaPayload {
  generated_at: string;
  last_successful_overall_update: string;
  latest_market_date: string | null;
  score_version: string;
  universe_size: number;
  successful_symbols: number;
  failed_symbols: number;
  sources: SourceRunStatus[];
  warnings: string[];
  legal_notice: string;
}

export interface HistoryPoint {
  date: string;
  price: number | null;
  daily_return_pct: number | null;
  volume: number | null;
  volume_ratio_30d: number | null;
  wikipedia_pageviews: number | null;
  wikipedia_change_pct: number | null;
  short_volume_ratio: number | null;
  attention_score: number | null;
  trading_score: number | null;
  retail_proxy_score: number | null;
  impact_score: number | null;
  hype_score: number | null;
  confidence_score: number | null;
  data_status: DataStatus;
}

export interface SymbolHistoryPayload {
  symbol: string;
  company_name: string;
  generated_at: string;
  score_version: string;
  points: HistoryPoint[];
  sources: SourceRunStatus[];
  limitations: string[];
}

export interface DashboardData {
  latest: LatestPayload;
  meta: MetaPayload;
}
