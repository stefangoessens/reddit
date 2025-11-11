
'use client';

import { useMemo, useState } from 'react';

import { AlertsFeed } from '@/components/AlertsFeed';
import { Heatboard } from '@/components/Heatboard';
import { SavedSnapshotsPanel } from '@/components/SavedSnapshotsPanel';
import { TrendingTable } from '@/components/TrendingTable';
import { useTrending, type TrendingWindow } from '@/hooks/useTrending';
import { useTrendingSnapshots } from '@/hooks/useTrendingSnapshots';

const timeframeOptions: { value: TrendingWindow; label: string; description: string }[] = [
  { value: '5m', label: '5M', description: 'Burst detector window' },
  { value: '1h', label: '1H', description: 'Short-term trend' },
  { value: '24h', label: '24H', description: 'Rolling day' },
  { value: '7d', label: '7D', description: 'Weekly view' },
  { value: '30d', label: '30D', description: 'Monthly context' },
];

export default function HomePage() {
  const [timeframe, setTimeframe] = useState<TrendingWindow>('5m');
  const { tickers, isLoading, isError } = useTrending(timeframe, 30);
  const { snapshots, saveSnapshot, deleteSnapshot, clearSnapshots } = useTrendingSnapshots();
  const topForHeatboard = useMemo(() => tickers.slice(0, 6), [tickers]);
  const canSaveSnapshot = tickers.length > 0 && !isLoading;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-widest text-amber-400">Now</p>
        <h1 className="text-4xl font-bold mt-2">WallStreetBets Hype Radar</h1>
        <p className="text-slate-400 mt-2">
          {isLoading && 'Loading live hype…'}
          {isError && 'Unable to load data right now. Check API connectivity.'}
          {!isLoading && !isError && 'Live hype across WallStreetBets tickers.'}
        </p>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2">
          {timeframeOptions.map((option) => (
            <button
              key={option.value}
              title={option.description}
              onClick={() => setTimeframe(option.value)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
                timeframe === option.value
                  ? 'bg-amber-400 text-slate-900'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => saveSnapshot(timeframe, tickers)}
          disabled={!canSaveSnapshot}
          className="self-start rounded-lg border border-amber-500 bg-transparent px-4 py-2 text-sm font-semibold text-amber-300 transition-colors hover:bg-amber-500/10 disabled:cursor-not-allowed disabled:border-slate-700 disabled:text-slate-500"
        >
          Save record
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Heatboard data={topForHeatboard} />
          <TrendingTable data={tickers} />
        </div>
        <div className="space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-2">Live Alerts</h2>
            <AlertsFeed />
          </section>
          <SavedSnapshotsPanel
            snapshots={snapshots}
            onDelete={deleteSnapshot}
            onClear={clearSnapshots}
          />
        </div>
      </div>
    </section>
  );
}
