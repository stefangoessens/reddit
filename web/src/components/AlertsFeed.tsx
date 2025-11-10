'use client';

import { useAlerts } from '@/hooks/useAlerts';

export function AlertsFeed() {
  const alerts = useAlerts();

  if (!alerts.length) {
    return (<div className="border border-dashed border-slate-700 rounded-lg p-4 text-sm text-slate-400">Alerts will appear here once the detector starts emitting heads-up or actionable events.</div>);
  }
  return (<ul className="space-y-2 max-h-64 overflow-y-auto">{alerts.map((alert) => (<li key={`${alert.ts}-${alert.ticker}`} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3"><div className="flex items-center justify-between text-sm"><span className="font-semibold text-slate-100">{alert.ticker}</span><span className="text-xs text-slate-400">{new Date(alert.ts).toLocaleTimeString()}</span></div><div className="text-xs text-slate-400 mt-1">{alert.tier.toUpperCase()} · Hype {alert.hypeScore.toFixed(1)} · Price {alert.priceAtAlert?.toFixed(2) ?? '—'}</div></li>))}</ul>);
}
