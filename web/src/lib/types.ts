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
  sparkline?: number[];
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

export type MentionSeriesPoint = {
  ts: string;
  mentions: number;
  unique_authors: number;
  avg_sentiment: number;
  zscore: number;
};

export type TickerMentionsResponse = {
  series: MentionSeriesPoint[];
};

export type ImpactWindowStats = Record<string, number>;

export type TickerImpactResponse = {
  samples: number;
  avg: ImpactWindowStats;
  car?: ImpactWindowStats;
};

export type PosterLeaderboardRow = {
  author: string;
  n: number;
  alpha_1d_med: number;
  alpha_1h_med?: number;
  win_rate: number;
  early_score?: number;
  last_called_at?: string;
};
