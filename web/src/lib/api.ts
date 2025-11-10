import type { TrendingTicker } from './types';

// Hardcoded for Railway deployment - environment variable not being picked up during build
const API_BASE = 'https://reddit-production-e3de.up.railway.app';

export async function fetchTrending(): Promise<TrendingTicker[]> {
  const response = await fetch(`${API_BASE}/v1/trending?window=5m`);
  if (!response.ok) {
    throw new Error('Failed to load trending data');
  }
  return response.json();
}
