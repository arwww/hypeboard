import { useEffect, useState } from 'react';

import { loadDashboardData } from '../services/dataService';
import type { DashboardData } from '../types/data';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useDashboardData(): AsyncState<DashboardData> {
  const [state, setState] = useState<AsyncState<DashboardData>>({
    data: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();
    loadDashboardData(controller.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          data: null,
          loading: false,
          error: error instanceof Error ? error.message : 'Unknown data loading error',
        });
      });
    return () => controller.abort();
  }, []);

  return state;
}
