'use client';

import type { TrendingTicker } from '@/lib/types';
import { SentimentBadge } from './SentimentBadge';

export type HeatboardProps = {
  data: TrendingTicker[];
};

export function Heatboard({ data }: HeatboardProps) {
  if (!data.length) {
    return (
      <div className="border border-dashed border-slate-700 rounded-lg p-6 text-center">
        <p className="text-slate-400">No trending tickers yet. Connect the API to light this up.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.map((ticker) => (
        <article
          key={ticker.ticker}
          className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-lg"
        >
          <header className="flex items-baseline justify-between">
            <h3 className="text-2xl font-semibold tracking-tight">{ticker.ticker}</h3>
            <span className="text-xs text-slate-400">z={ticker.zscore.toFixed(1)}</span>
          </header>
          <dl className="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-300">
            <div>
              <dt className="text-slate-500">Mentions</dt>
              <dd className="text-lg font-semibold">{ticker.mentions}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Authors</dt>
              <dd className="text-lg font-semibold">{ticker.unique_authors}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Hype</dt>
              <dd className="text-lg font-semibold">{ticker.hype_score.toFixed(1)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">First seen</dt>
              <dd className="text-lg font-semibold">
                {new Intl.DateTimeFormat('en', {
                  hour: '2-digit',
                  minute: '2-digit',
                }).format(new Date(ticker.first_seen))}
              </dd>
            </div>
          </dl>
          <div className="mt-4">
            <SentimentBadge avgSentiment={ticker.avg_sentiment} />
          </div>
        </article>
      ))}
    </div>
  );
}
