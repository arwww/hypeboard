import type { DashboardData, LatestPayload, MetaPayload, SymbolHistoryPayload } from '../types/data';

const basePath = `${import.meta.env.BASE_URL}data`;

async function loadJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    signal,
    cache: 'no-cache',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Data request failed (${response.status}) for ${path}`);
  }
  return (await response.json()) as T;
}

export async function loadDashboardData(signal?: AbortSignal): Promise<DashboardData> {
  const [latest, meta] = await Promise.all([
    loadJson<LatestPayload>(`${basePath}/latest.json`, signal),
    loadJson<MetaPayload>(`${basePath}/meta.json`, signal),
  ]);
  return { latest, meta };
}

export async function loadSymbolHistory(
  symbol: string,
  signal?: AbortSignal,
): Promise<SymbolHistoryPayload> {
  const safeSymbol = symbol.toUpperCase().replace(/[^A-Z0-9.-]/g, '');
  if (!safeSymbol) {
    throw new Error('Invalid symbol');
  }
  return loadJson<SymbolHistoryPayload>(`${basePath}/history/${safeSymbol}.json`, signal);
}
