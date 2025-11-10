export type TrendingTicker = {
  ticker: string;
  mentions: number;
  unique_authors: number;
  zscore: number;
  avg_sentiment: number;
  hype_score: number;
  first_seen: string;
  window?: string;
  last_price?: number;
};

export type AlertEvent = {
  ts: string;
  ticker: string;
  tier: 'heads-up' | 'actionable';
  hype_score: number;
  zscore: number;
  unique_authors: number;
  threads_touched: number;
  avg_sentiment: number;
  price_at_alert?: number;
};
