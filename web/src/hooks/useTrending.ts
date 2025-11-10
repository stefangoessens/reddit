'use client';

import useSWR from 'swr';

import type { TrendingTicker } from '@/lib/types';

const fetcher = (url: string) =>
  fetch(url).then((res) => {
    if (!res.ok) throw new Error('Failed to load trending data');
    return res.json();
  });

export function useTrending(window = '5m') {
  // Hardcoded for Railway deployment - environment variable not being picked up during build
  const apiBase = 'https://reddit-production-e3de.up.railway.app';
  const { data, error, isLoading } = useSWR<TrendingTicker[]>(
    `${apiBase}/v1/trending?window=${window}`,
    fetcher,
    { refreshInterval: 30_000 },
  );
  return {
    tickers: data ?? [],
    isLoading,
    isError: Boolean(error),
  };
}
