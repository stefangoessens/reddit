'use client';

import useSWR from 'swr';

import type { TrendingTicker } from '@/lib/types';
import { API_BASE } from '@/lib/env';

export type TrendingWindow = '5m' | '1h' | '24h' | '7d' | '30d';

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to load trending data');
    return res.json();
  });

export function useTrending(window: TrendingWindow = '5m', limit = 20) {
  const { data, error, isLoading } = useSWR<TrendingTicker[]>(
    `${API_BASE}/v1/trending?window=${window}&limit=${limit}`,
    fetcher,
    { refreshInterval: 30_000 },
  );
  return {
    tickers: data ?? [],
    isLoading,
    isError: Boolean(error),
  };
}
