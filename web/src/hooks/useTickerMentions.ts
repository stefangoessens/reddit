'use client';

import useSWR from 'swr';

import { API_BASE } from '@/lib/env';
import type { MentionSeriesPoint, TickerMentionsResponse } from '@/lib/types';

export type MentionLookback = '1h' | '24h' | '7d';

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Failed to load ticker mentions');
  }
  return (await res.json()) as TickerMentionsResponse;
};

function getWindowStart(window: MentionLookback) {
  const now = Date.now();
  const msMap: Record<MentionLookback, number> = {
    '1h': 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
  };
  return new Date(now - msMap[window]).toISOString();
}

export function useTickerMentions(symbol: string, window: MentionLookback, granularity = '1m') {
  const start = getWindowStart(window);
  const end = new Date().toISOString();
  const params = new URLSearchParams({ granularity, start, end }).toString();
  const key = symbol ? `${API_BASE}/v1/tickers/${symbol}/mentions?${params}` : null;
  const { data, error, isLoading } = useSWR<TickerMentionsResponse>(key, fetcher, {
    refreshInterval: 60_000,
  });
  return {
    series: data?.series ?? ([] as MentionSeriesPoint[]),
    isLoading,
    isError: Boolean(error),
  };
}
