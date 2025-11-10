'use client';

import { useState } from 'react';
import { AlertsFeed } from '@/components/AlertsFeed';
import { TrendingTable } from '@/components/TrendingTable';
import { useTrending } from '@/hooks/useTrending';

type Timeframe = '1h' | '24h' | '7d' | '30d';

export default function HomePage() {
  const [timeframe, setTimeframe] = useState<Timeframe>('1h');
  const { tickers, isLoading, isError } = useTrending(timeframe);

  const timeframes: { value: Timeframe; label: string }[] = [
    { value: '1h', label: '1H' },
    { value: '24h', label: '24H' },
    { value: '7d', label: '7D' },
    { value: '30d', label: '30D' },
  ];

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

      <div className="flex gap-2">
        {timeframes.map((tf) => (
          <button
            key={tf.value}
            onClick={() => setTimeframe(tf.value)}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
              timeframe === tf.value
                ? 'bg-amber-400 text-slate-900'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {tf.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrendingTable data={tickers} />
        </div>
        <div className="space-y-3">
          <h2 className="text-xl font-semibold">Live Alerts</h2>
          <AlertsFeed />
        </div>
      </div>
    </section>
  );
}
