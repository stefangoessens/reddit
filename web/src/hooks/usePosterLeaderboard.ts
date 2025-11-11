'use client';

import useSWR from 'swr';

import { API_BASE } from '@/lib/env';
import type { PosterLeaderboardRow } from '@/lib/types';

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error('Failed to load leaderboard');
  }
  return (await res.json()) as PosterLeaderboardRow[];
};

export function usePosterLeaderboard(metric = 'alpha_1d', minCalls = 5, window = '30d') {
  const params = new URLSearchParams({ metric, min_calls: String(minCalls), window });
  const key = `${API_BASE}/v1/posters/leaderboard?${params}`;
  const { data, error, isLoading } = useSWR<PosterLeaderboardRow[]>(key, fetcher, {
    refreshInterval: 5 * 60_000,
  });
  return {
    rows: data ?? [],
    isLoading,
    isError: Boolean(error),
  };
}
