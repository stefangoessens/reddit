import { API_BASE } from './env';
import type { TrendingTicker } from './types';

export async function fetchTrending(): Promise<TrendingTicker[]> {
  const response = await fetch(`${API_BASE}/v1/trending?window=5m`);
  if (!response.ok) {
    throw new Error('Failed to load trending data');
  }
  return response.json();
}
