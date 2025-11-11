'use client';

import { useCallback, useEffect, useState } from 'react';

import type { TrendingTicker } from '@/lib/types';
import type { TrendingWindow } from './useTrending';

export type TrendingSnapshot = {
  id: string;
  timeframe: TrendingWindow;
  capturedAt: string;
  tickers: TrendingTicker[];
};

const STORAGE_KEY = 'wsb-trending-snapshots';
const MAX_SNAPSHOTS = 10;

function safeParseSnapshots(raw: string | null): TrendingSnapshot[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as TrendingSnapshot[];
    if (!Array.isArray(parsed)) return [];
    return parsed;
  } catch {
    return [];
  }
}

export function useTrendingSnapshots() {
  const [snapshots, setSnapshots] = useState<TrendingSnapshot[]>(() => {
    if (typeof window === 'undefined') {
      return [];
    }
    return safeParseSnapshots(window.localStorage.getItem(STORAGE_KEY));
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshots));
    } catch {
      // Ignore storage writes when quota is exceeded or unavailable.
    }
  }, [snapshots]);

  const saveSnapshot = useCallback((timeframe: TrendingWindow, tickers: TrendingTicker[]) => {
    if (!tickers.length) return;
    const id = typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const snapshot: TrendingSnapshot = {
      id,
      timeframe,
      capturedAt: new Date().toISOString(),
      tickers,
    };
    setSnapshots((prev) => [snapshot, ...prev].slice(0, MAX_SNAPSHOTS));
  }, []);

  const deleteSnapshot = useCallback((id: string) => {
    setSnapshots((prev) => prev.filter((snapshot) => snapshot.id !== id));
  }, []);

  const clearSnapshots = useCallback(() => {
    setSnapshots([]);
  }, []);

  return {
    snapshots,
    saveSnapshot,
    deleteSnapshot,
    clearSnapshots,
  };
}
