'use client';

import { useMemo, useState } from 'react';

import { useTickerImpact } from '@/hooks/useTickerImpact';
import { MentionLookback, useTickerMentions } from '@/hooks/useTickerMentions';
import type { MentionSeriesPoint } from '@/lib/types';

const LOOKBACK_OPTIONS: { value: MentionLookback; label: string }[] = [
  { value: '1h', label: '1H' },
  { value: '24h', label: '24H' },
  { value: '7d', label: '7D' },
];

function LineChart({ series }: { series: MentionSeriesPoint[] }) {
  if (!series.length) return (
    <div className="h-60 rounded-xl border border-dashed border-slate-800 flex items-center justify-center text-sm text-slate-500">
      No data yet. Keep ingestion + trend services running.
    </div>
  );

  const values = series.map((point) => point.mentions);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const points = series
    .map((point, index) => {
      const x = (index / (series.length - 1 || 1)) * 100;
      const y = 100 - ((point.mentions - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="h-60 w-full">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full">
        <polyline
          fill="none"
          stroke="#facc15"
          strokeWidth="2"
          strokeLinecap="round"
          points={points}
        />
      </svg>
    </div>
  );
}

function MetricCard({ label, value, helper }: { label: string; value: string; helper?: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="text-2xl font-semibold text-slate-100">{value}</p>
      {helper && <p className="text-xs text-slate-500 mt-1">{helper}</p>}
    </div>
  );
}

function ImpactTable({
  stats,
}: {
  stats?: { samples: number; avg: Record<string, number>; car?: Record<string, number> };
}) {
  if (!stats) {
    return (
      <div className="rounded-xl border border-dashed border-slate-800 p-4 text-sm text-slate-500">
        No impact runs yet.
      </div>
    );
  }

  const windows = Object.keys(stats.avg ?? {});

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/30">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 text-sm text-slate-400">
        <span>Samples: {stats.samples}</span>
        {stats.car && <span>CAR window(s): {Object.keys(stats.car).join(', ')}</span>}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-2">Window</th>
            <th className="px-4 py-2">Avg Return</th>
            {stats.car && <th className="px-4 py-2">CAR</th>}
          </tr>
        </thead>
        <tbody>
          {windows.map((window) => (
            <tr key={window} className="border-t border-slate-900">
              <td className="px-4 py-2 text-slate-300">{window}</td>
              <td className="px-4 py-2 text-amber-300">{(stats.avg[window] * 100).toFixed(2)}%</td>
              {stats.car && (
                <td className="px-4 py-2 text-emerald-300">
                  {stats.car[window] !== undefined ? `${(stats.car[window] * 100).toFixed(2)}%` : '—'}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface PageProps {
  params: { sym: string };
}

export default function TickerPage({ params }: PageProps) {
  const symbol = params.sym.toUpperCase();
  const [lookback, setLookback] = useState<MentionLookback>('24h');
  const { series, isLoading } = useTickerMentions(symbol, lookback);
  const { impact } = useTickerImpact(symbol, lookback);

  const latest = series[series.length - 1];
  const prev = series[series.length - 2];
  const mentionDelta = latest && prev ? latest.mentions - prev.mentions : 0;

  const sentimentRange = useMemo(() => {
    if (!series.length) return { max: 0, min: 0 };
    const sentiments = series.map((point) => point.avg_sentiment);
    return { max: Math.max(...sentiments), min: Math.min(...sentiments) };
  }, [series]);

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-4">
          <h1 className="text-4xl font-bold">{symbol}</h1>
          <div className="flex gap-2">
            {LOOKBACK_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setLookback(option.value)}
                className={`rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${
                  option.value === lookback ? 'bg-amber-400 text-slate-950' : 'bg-slate-900 text-slate-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <p className="text-slate-400">
          Minute-level mentions, sentiment, and impact pulled straight from `/v1/tickers/{symbol}/mentions` and
          `/impact`.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Mentions"
          value={latest ? latest.mentions.toLocaleString() : isLoading ? '...' : '0'}
          helper={mentionDelta ? `${mentionDelta > 0 ? '+' : ''}${mentionDelta} vs prev minute` : 'Waiting for data'}
        />
        <MetricCard
          label="Unique authors"
          value={latest ? latest.unique_authors.toLocaleString() : isLoading ? '...' : '0'}
        />
        <MetricCard
          label="Avg sentiment"
          value={latest ? `${(latest.avg_sentiment * 100).toFixed(1)}%` : isLoading ? '...' : 'n/a'}
          helper={`Range ${Math.round(sentimentRange.min * 100)}% → ${Math.round(sentimentRange.max * 100)}%`}
        />
      </div>

      <div className="space-y-4">
        <header className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">Mentions timeline</h2>
          <span className="text-sm text-slate-500">Granularity: 1m buckets</span>
        </header>
        <LineChart series={series} />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Mentions</th>
                <th className="px-3 py-2">Authors</th>
                <th className="px-3 py-2">Sentiment</th>
                <th className="px-3 py-2">Z-Score</th>
              </tr>
            </thead>
            <tbody>
              {series.slice(-60).reverse().map((point) => (
                <tr key={point.ts} className="border-t border-slate-900">
                  <td className="px-3 py-2 text-slate-400">
                    {new Date(point.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-3 py-2 font-semibold text-slate-100">{point.mentions}</td>
                  <td className="px-3 py-2 text-slate-300">{point.unique_authors}</td>
                  <td className="px-3 py-2 text-slate-300">{(point.avg_sentiment * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-amber-300">{point.zscore.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Impact (forward returns)</h2>
        <ImpactTable stats={impact} />
      </div>
    </section>
  );
}
