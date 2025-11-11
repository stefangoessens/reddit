'use client';

import type { TrendingTicker } from '@/lib/types';
import { SentimentBadge } from './SentimentBadge';

function Sparkline({ values }: { values: number[] }) {
  if (!values.length) return null;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1 || 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg viewBox="0 0 100 100" className="h-12 w-full">
      <polyline
        fill="none"
        stroke="url(#sparklineGradient)"
        strokeWidth="2"
        strokeLinecap="round"
        points={points}
      />
      <defs>
        <linearGradient id="sparklineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#facc15" />
          <stop offset="100%" stopColor="#f97316" />
        </linearGradient>
      </defs>
    </svg>
  );
}

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
      {data.map((ticker) => {
        const bursty = ticker.zscore >= 3 && ticker.unique_authors >= 3;
        const delta = ticker.sparkline && ticker.sparkline.length >= 2
          ? ticker.sparkline[ticker.sparkline.length - 1] - ticker.sparkline[0]
          : null;
        return (
        <article
          key={ticker.ticker}
          className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 shadow-lg"
        >
          <header className="flex items-center justify-between gap-2">
            <div>
              <h3 className="text-2xl font-semibold tracking-tight">{ticker.ticker}</h3>
              <p className="text-xs text-slate-500">Z {ticker.zscore.toFixed(1)} · Hype {ticker.hype_score.toFixed(1)}</p>
            </div>
            {bursty && (
              <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300">
                EARLY
              </span>
            )}
          </header>
          <div className="mt-3">
            {ticker.sparkline && ticker.sparkline.length > 1 ? (
              <Sparkline values={ticker.sparkline} />
            ) : (
              <div className="h-12 rounded-lg border border-dashed border-slate-800 text-center text-xs text-slate-500 flex items-center justify-center">
                Sparkline coming soon
              </div>
            )}
            {delta !== null && (
              <p className="mt-1 text-xs text-slate-500">
                {delta >= 0 ? '+' : ''}{delta.toFixed(1)} mentions vs. start of window
              </p>
            )}
          </div>
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
        );
      })}
    </div>
  );
}
