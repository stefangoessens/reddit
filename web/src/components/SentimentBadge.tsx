import React from 'react';

const sentimentCopy = (
  avgSentiment: number,
): { label: string; color: string } => {
  if (avgSentiment >= 0.15) {
    return { label: 'Bullish', color: 'bg-emerald-500/20 text-emerald-300' };
  }
  if (avgSentiment <= -0.15) {
    return { label: 'Bearish', color: 'bg-rose-500/20 text-rose-300' };
  }
  return { label: 'Neutral', color: 'bg-slate-500/20 text-slate-200' };
};

export function SentimentBadge({ avgSentiment }: { avgSentiment: number }) {
  const badge = sentimentCopy(avgSentiment);

  return (
    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${badge.color}`}>
      <span>{badge.label}</span>
      <span className="text-xs text-slate-400">{avgSentiment.toFixed(2)}</span>
    </span>
  );
}
