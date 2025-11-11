'use client';

import type { TrendingSnapshot } from '@/hooks/useTrendingSnapshots';

type SavedSnapshotsPanelProps = {
  snapshots: TrendingSnapshot[];
  onDelete: (id: string) => void;
  onClear: () => void;
};

export function SavedSnapshotsPanel({ snapshots, onDelete, onClear }: SavedSnapshotsPanelProps) {
  return (
    <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-100">Saved records</h2>
          <p className="text-xs text-slate-500">Capture any snapshot to compare later.</p>
        </div>
        {snapshots.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Clear all
          </button>
        )}
      </div>

      {snapshots.length === 0 ? (
        <p className="text-sm text-slate-500">
          No records yet. Use the “Save record” button once the board looks interesting.
        </p>
      ) : (
        <ul className="space-y-3">
          {snapshots.map((snapshot) => (
            <li key={snapshot.id} className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-3">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <div>
                  <p className="font-semibold text-slate-100">{snapshot.timeframe.toUpperCase()} window</p>
                  <p>{new Date(snapshot.capturedAt).toLocaleString()}</p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(snapshot.id)}
                  className="text-xs text-slate-400 hover:text-slate-200"
                >
                  Remove
                </button>
              </div>
              <ol className="mt-2 space-y-1 text-xs text-slate-400">
                {snapshot.tickers.slice(0, 3).map((ticker, index) => (
                  <li key={`${snapshot.id}-${ticker.ticker}`}>
                    #{index + 1} {ticker.ticker} — mentions {ticker.mentions}, hype {ticker.hype_score.toFixed(1)}
                  </li>
                ))}
              </ol>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
