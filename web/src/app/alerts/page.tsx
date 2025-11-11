'use client';

import { useMemo, useState } from 'react';

import { useAlerts } from '@/hooks/useAlerts';

const TIER_FILTERS = ['all', 'heads-up', 'actionable'] as const;

type TierFilter = (typeof TIER_FILTERS)[number];

export default function AlertsPage() {
  const alerts = useAlerts(100);
  const [filter, setFilter] = useState<TierFilter>('all');

  const filteredAlerts = useMemo(() => {
    if (filter === 'all') return alerts;
    return alerts.filter((alert) => alert.tier === filter);
  }, [alerts, filter]);

  const actionableRate = useMemo(() => {
    if (!alerts.length) return 0;
    const actionable = alerts.filter((alert) => alert.tier === 'actionable').length;
    return (actionable / alerts.length) * 100;
  }, [alerts]);

  return (
    <section className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-4xl font-bold">Live Alerts</h1>
        <p className="text-slate-400 text-sm">
          Streaming from `/v1/alerts/live`. Use the tier filters to focus on actionable bursts or keep the full tape running for
          heads-up signals.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Alerts captured</p>
          <p className="text-3xl font-semibold text-slate-100">{alerts.length}</p>
          <p className="text-xs text-slate-500">Rolling buffer of 100</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Actionable rate</p>
          <p className="text-3xl font-semibold text-emerald-300">{actionableRate.toFixed(1)}%</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Current filter</p>
          <p className="text-3xl font-semibold text-slate-100">{filter.toUpperCase()}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {TIER_FILTERS.map((tier) => (
          <button
            key={tier}
            onClick={() => setFilter(tier)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              filter === tier ? 'bg-amber-400 text-slate-950' : 'bg-slate-900 text-slate-200 hover:bg-slate-800'
            }`}
          >
            {tier.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Ticker</th>
              <th className="px-3 py-2">Tier</th>
              <th className="px-3 py-2">Hype</th>
              <th className="px-3 py-2">Z-Score</th>
              <th className="px-3 py-2">Authors</th>
              <th className="px-3 py-2">Sentiment</th>
              <th className="px-3 py-2">Price</th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.map((alert) => (
              <tr key={`${alert.ts}-${alert.ticker}`} className="border-t border-slate-900">
                <td className="px-3 py-2 text-slate-400">
                  {new Date(alert.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </td>
                <td className="px-3 py-2 font-semibold text-slate-100">{alert.ticker}</td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-semibold ${
                      alert.tier === 'actionable'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-sky-500/20 text-sky-300'
                    }`}
                  >
                    {alert.tier.toUpperCase()}
                  </span>
                </td>
                <td className="px-3 py-2 text-amber-300">{alert.hype_score.toFixed(1)}</td>
                <td className="px-3 py-2 text-amber-200">{alert.zscore.toFixed(2)}</td>
                <td className="px-3 py-2 text-slate-300">{alert.unique_authors}</td>
                <td className="px-3 py-2 text-slate-300">{(alert.avg_sentiment * 100).toFixed(1)}%</td>
                <td className="px-3 py-2 text-slate-300">
                  {alert.price_at_alert ? `$${alert.price_at_alert.toFixed(2)}` : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
