export type TrendingTicker = {
  ticker: string;
  mentions: number;
  uniqueAuthors: number;
  zscore: number;
  avgSentiment: number;
  hypeScore: number;
  firstSeen: string;
  window?: string;
  lastPrice?: number;
};

export type AlertEvent = {
  ts: string;
  ticker: string;
  tier: 'heads-up' | 'actionable';
  hypeScore: number;
  zscore: number;
  uniqueAuthors: number;
  threadsTouched: number;
  avgSentiment: number;
  priceAtAlert?: number;
};
