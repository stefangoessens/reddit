import type { TrendingTicker } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8080';

export async function fetchTrending(): Promise<TrendingTicker[]> {
  const response = await fetch(`${API_BASE}/v1/trending?window=5m`);
  if (!response.ok) {
    throw new Error('Failed to load trending data');
  }
  return response.json();
}
