'use client';

import useSWR from 'swr';

import { API_BASE } from '@/lib/env';
import type { TickerImpactResponse } from '@/lib/types';

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Failed to load ticker impact');
  }
  return (await res.json()) as TickerImpactResponse;
};

export function useTickerImpact(symbol: string, window = '7d') {
  const key = symbol ? `${API_BASE}/v1/tickers/${symbol}/impact?window=${window}` : null;
  const { data, error, isLoading } = useSWR<TickerImpactResponse>(key, fetcher, {
    refreshInterval: 5 * 60_000,
  });
  return {
    impact: data,
    isLoading,
    isError: Boolean(error),
  };
}
