import { createOpenAI } from '@ai-sdk/openai';
import { streamText, type CoreMessage } from 'ai';

import { API_BASE } from '@/lib/env';
import type { AlertEvent, TrendingTicker } from '@/lib/types';

const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const MAX_TICKERS = 15;
const DEFAULT_TIMEFRAME = '1h';

type DashboardPayload = {
  timeframe?: string;
  tickers?: TrendingTicker[];
  alerts?: AlertEvent[];
  asOf?: string;
};

type DashboardSnapshot = {
  timeframe: string;
  tickers: TrendingTicker[];
  alerts: AlertEvent[];
  asOf: string;
  source: 'api' | 'client' | 'none';
};

async function fetchTrendingFromApi(timeframe: string, limit: number): Promise<TrendingTicker[] | null> {
  try {
    const response = await fetch(`${API_BASE}/v1/trending?window=${encodeURIComponent(timeframe)}&limit=${limit}`, {
      cache: 'no-store',
    });
    if (!response.ok) {
      console.warn('Trending fetch failed', response.status, response.statusText);
      return null;
    }
    return (await response.json()) as TrendingTicker[];
  } catch (error) {
    console.warn('Trending fetch error', error);
    return null;
  }
}

async function buildDashboardSnapshot(payload?: DashboardPayload): Promise<DashboardSnapshot> {
  const timeframe = payload?.timeframe ?? DEFAULT_TIMEFRAME;
  const apiTickers = await fetchTrendingFromApi(timeframe, MAX_TICKERS);
  const tickers = apiTickers && apiTickers.length
    ? apiTickers
    : payload?.tickers?.slice(0, MAX_TICKERS) ?? [];
  const alerts = payload?.alerts?.slice(0, 5) ?? [];
  const asOf = payload?.asOf ?? new Date().toISOString();
  const source: DashboardSnapshot['source'] = apiTickers && apiTickers.length
    ? 'api'
    : tickers.length
      ? 'client'
      : 'none';
  return { timeframe, tickers, alerts, asOf, source };
}

function formatSentiment(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'n/a';
  }
  const percent = (value * 100).toFixed(0);
  const prefix = value > 0 ? '+' : '';
  return `${prefix}${percent}%`;
}

function describeTicker(ticker: TrendingTicker) {
  return `${ticker.ticker}: hype ${ticker.hype_score.toFixed(1)}, mentions ${ticker.mentions}, authors ${ticker.unique_authors}, z ${ticker.zscore.toFixed(2)}, sentiment ${formatSentiment(ticker.avg_sentiment)}`;
}

function formatTrendingNarrative(snapshot: DashboardSnapshot) {
  if (!snapshot.tickers.length) {
    return `No trending tickers supplied for the ${snapshot.timeframe} window.`;
  }
  const top = snapshot.tickers.slice(0, 5).map(describeTicker).join('; ');
  const mentionLeader = snapshot.tickers.reduce((best, current) => (current.mentions > best.mentions ? current : best));
  const sentimentHigh = snapshot.tickers.reduce((best, current) => (current.avg_sentiment > best.avg_sentiment ? current : best));
  const sentimentLow = snapshot.tickers.reduce((best, current) => (current.avg_sentiment < best.avg_sentiment ? current : best));
  const zSpike = snapshot.tickers.reduce((best, current) => (current.zscore > best.zscore ? current : best));
  return [
    `Trending snapshot (${snapshot.timeframe} window) top hype entries: ${top}.`,
    `${mentionLeader.ticker} leads mentions at ${mentionLeader.mentions}.`,
    `${zSpike.ticker} shows the sharpest z-score spike at ${zSpike.zscore.toFixed(2)}.`,
    `Sentiment spans from ${sentimentLow.ticker} (${formatSentiment(sentimentLow.avg_sentiment)}) to ${sentimentHigh.ticker} (${formatSentiment(sentimentHigh.avg_sentiment)}).`,
  ].join(' ');
}

function formatAlertsNarrative(alerts: AlertEvent[]) {
  if (!alerts.length) {
    return 'No live alerts captured yet.';
  }
  const rows = alerts.slice(0, 5).map((alert) => {
    const timestamp = new Date(alert.ts).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
    return `${timestamp} ${alert.ticker} (${alert.tier}) hype ${alert.hype_score.toFixed(1)}, authors ${alert.unique_authors}, sentiment ${formatSentiment(alert.avg_sentiment)}`;
  });
  return `Recent alert tape (latest first): ${rows.join('; ')}.`;
}

function buildDashboardNarrative(snapshot: DashboardSnapshot) {
  return [
    `Dashboard data as of ${snapshot.asOf} (source: ${snapshot.source}).`,
    formatTrendingNarrative(snapshot),
    formatAlertsNarrative(snapshot.alerts),
    'Reference these numbers directly when answering and call out notable divergences, spikes, or risk signals.',
  ].join('\n\n');
}

export async function POST(req: Request) {
  if (!process.env.OPENAI_API_KEY) {
    return new Response('Missing OPENAI_API_KEY environment variable', { status: 500 });
  }

  const { messages, dashboard } = (await req.json()) as { messages?: CoreMessage[]; dashboard?: DashboardPayload };

  if (!Array.isArray(messages)) {
    return new Response('`messages` array is required', { status: 400 });
  }

  const snapshot = await buildDashboardSnapshot(dashboard);
  const dashboardNarrative = buildDashboardNarrative(snapshot);
  const systemPrompt = [
    'You are a helpful WallStreetBets market intel assistant. Be concise, quantify hype, and mention relevant tickers.',
    dashboardNarrative,
  ].join('\n\n');

  try {
    const result = await streamText({
      model: openai('gpt-4o-mini'),
      system: systemPrompt,
      messages,
    });

    return result.toAIStreamResponse();
  } catch (error) {
    console.error('AI route error', error);
    return new Response('Unable to generate response', { status: 500 });
  }
}
