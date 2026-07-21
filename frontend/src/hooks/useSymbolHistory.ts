import { useEffect, useState } from 'react';

import { loadSymbolHistory } from '../services/dataService';
import type { SymbolHistoryPayload } from '../types/data';

export function useSymbolHistory(symbol: string | undefined) {
  const [data, setData] = useState<SymbolHistoryPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) {
      setLoading(false);
      setError('No symbol provided');
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    loadSymbolHistory(symbol, controller.signal)
      .then((payload) => {
        setData(payload);
        setLoading(false);
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : 'Could not load symbol history');
        setLoading(false);
      });
    return () => controller.abort();
  }, [symbol]);

  return { data, loading, error };
}
