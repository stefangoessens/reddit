'use client';

import { useState } from 'react';
import type { TrendingTicker } from '@/lib/types';
import { SentimentBadge } from './SentimentBadge';

export type TrendingTableProps = {
  data: TrendingTicker[];
};

type SortField = 'ticker' | 'mentions' | 'unique_authors' | 'hype_score' | 'avg_sentiment';
type SortDirection = 'asc' | 'desc';

export function TrendingTable({ data }: TrendingTableProps) {
  const [sortField, setSortField] = useState<SortField>('mentions');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  if (!data.length) {
    return (
      <div className="border border-dashed border-slate-700 rounded-lg p-6 text-center">
        <p className="text-slate-400">No trending tickers yet. Waiting for data...</p>
      </div>
    );
  }

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    const multiplier = sortDirection === 'asc' ? 1 : -1;

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return (aValue - bValue) * multiplier;
    }
    return String(aValue).localeCompare(String(bValue)) * multiplier;
  });

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="text-slate-600">⇅</span>;
    }
    return <span className="text-amber-400">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left p-3 text-sm font-semibold text-slate-400">
              Rank
            </th>
            <th
              className="text-left p-3 text-sm font-semibold text-slate-400 cursor-pointer hover:text-slate-200"
              onClick={() => handleSort('ticker')}
            >
              Ticker <SortIcon field="ticker" />
            </th>
            <th
              className="text-right p-3 text-sm font-semibold text-slate-400 cursor-pointer hover:text-slate-200"
              onClick={() => handleSort('mentions')}
            >
              Mentions <SortIcon field="mentions" />
            </th>
            <th
              className="text-right p-3 text-sm font-semibold text-slate-400 cursor-pointer hover:text-slate-200"
              onClick={() => handleSort('unique_authors')}
            >
              Authors <SortIcon field="unique_authors" />
            </th>
            <th
              className="text-right p-3 text-sm font-semibold text-slate-400 cursor-pointer hover:text-slate-200"
              onClick={() => handleSort('hype_score')}
            >
              Hype <SortIcon field="hype_score" />
            </th>
            <th className="text-right p-3 text-sm font-semibold text-slate-400">
              Z-Score
            </th>
            <th
              className="text-center p-3 text-sm font-semibold text-slate-400 cursor-pointer hover:text-slate-200"
              onClick={() => handleSort('avg_sentiment')}
            >
              Sentiment <SortIcon field="avg_sentiment" />
            </th>
            <th className="text-right p-3 text-sm font-semibold text-slate-400">
              Price
            </th>
            <th className="text-right p-3 text-sm font-semibold text-slate-400">
              First Seen
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((ticker, index) => (
            <tr
              key={ticker.ticker}
              className="border-b border-slate-800/50 hover:bg-slate-900/40 transition-colors"
            >
              <td className="p-3 text-slate-400 text-sm">
                #{index + 1}
              </td>
              <td className="p-3">
                <span className="text-lg font-bold text-slate-100">{ticker.ticker}</span>
              </td>
              <td className="p-3 text-right font-semibold text-slate-200">
                {ticker.mentions.toLocaleString()}
              </td>
              <td className="p-3 text-right text-slate-300">
                {ticker.unique_authors}
              </td>
              <td className="p-3 text-right font-semibold text-amber-400">
                {ticker.hype_score.toFixed(1)}
              </td>
              <td className="p-3 text-right text-slate-300">
                {ticker.zscore.toFixed(2)}
              </td>
              <td className="p-3 text-center">
                <SentimentBadge avgSentiment={ticker.avg_sentiment} />
              </td>
              <td className="p-3 text-right text-slate-300">
                {ticker.last_price ? `$${ticker.last_price.toFixed(2)}` : '—'}
              </td>
              <td className="p-3 text-right text-xs text-slate-500">
                {new Intl.DateTimeFormat('en', {
                  hour: '2-digit',
                  minute: '2-digit',
                }).format(new Date(ticker.first_seen))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
