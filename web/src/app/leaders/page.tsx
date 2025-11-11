'use client';

import { useState } from 'react';

import { usePosterLeaderboard } from '@/hooks/usePosterLeaderboard';

const METRICS = [
  { value: 'alpha_1d', label: '1D Alpha' },
  { value: 'alpha_1h', label: '1H Alpha' },
  { value: 'win_rate', label: 'Win Rate' },
];

export default function LeaderboardPage() {
  const [metric, setMetric] = useState(METRICS[0].value);
  const { rows, isLoading } = usePosterLeaderboard(metric, 5, '30d');

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-4xl font-bold">Poster Leaderboard</h1>
        <p className="text-slate-400 text-sm">
          Powered by `/v1/posters/leaderboard`. These metrics look at realized alpha after alert calls over the last 30 days.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {METRICS.map((entry) => (
          <button
            key={entry.value}
            onClick={() => setMetric(entry.value)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              metric === entry.value ? 'bg-amber-400 text-slate-950' : 'bg-slate-900 text-slate-200'
            }`}
          >
            {entry.label}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="px-3 py-2">Rank</th>
              <th className="px-3 py-2">Poster</th>
              <th className="px-3 py-2">Calls</th>
              <th className="px-3 py-2">Alpha 1D</th>
              <th className="px-3 py-2">Alpha 1H</th>
              <th className="px-3 py-2">Win Rate</th>
              <th className="px-3 py-2">Early Score</th>
              <th className="px-3 py-2">Last Call</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !isLoading && (
              <tr>
                <td colSpan={8} className="px-3 py-6 text-center text-slate-500">
                  No leaderboard data yet.
                </td>
              </tr>
            )}
            {rows.map((row, index) => (
              <tr key={row.author} className="border-t border-slate-900">
                <td className="px-3 py-2 text-slate-400">#{index + 1}</td>
                <td className="px-3 py-2 font-semibold text-slate-100">{row.author}</td>
                <td className="px-3 py-2 text-slate-300">{row.n}</td>
                <td className="px-3 py-2 text-emerald-300">{(row.alpha_1d_med * 100).toFixed(2)}%</td>
                <td className="px-3 py-2 text-emerald-300">{row.alpha_1h_med ? (row.alpha_1h_med * 100).toFixed(2) : '0.00'}%</td>
                <td className="px-3 py-2 text-slate-300">{(row.win_rate * 100).toFixed(1)}%</td>
                <td className="px-3 py-2 text-slate-300">{row.early_score ? row.early_score.toFixed(2) : '--'}</td>
                <td className="px-3 py-2 text-slate-300">
                  {row.last_called_at ? new Date(row.last_called_at).toLocaleString() : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
