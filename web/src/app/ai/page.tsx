'use client';

import Link from 'next/link';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useChat } from '@ai-sdk/react';

import { useAlerts } from '@/hooks/useAlerts';
import { useTrending } from '@/hooks/useTrending';

const TIMEFRAMES = ['1h', '24h', '7d', '30d'] as const;
type Timeframe = (typeof TIMEFRAMES)[number];
const CONTEXT_TICKER_LIMIT = 15;

export default function AiPlaygroundPage() {
  const { messages, sendMessage, status, stop, error } = useChat();
  const [input, setInput] = useState('');
  const [analysisWindow, setAnalysisWindow] = useState<Timeframe>('1h');
  const { tickers, isLoading: isTrendingLoading } = useTrending(analysisWindow, CONTEXT_TICKER_LIMIT);
  const alerts = useAlerts(5);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    await sendMessage(
      { text: trimmed },
      {
        body: {
          dashboard: {
            timeframe: analysisWindow,
            tickers: tickers.slice(0, CONTEXT_TICKER_LIMIT),
            alerts,
            asOf: new Date().toISOString(),
          },
        },
      },
    );
    setInput('');
  }

  const displayedTickers = tickers.slice(0, 6);
  const displayedAlerts = alerts.slice(0, 4);

  return (
    <section className="space-y-6">
      <Link href="/" className="text-sm text-slate-400 hover:text-slate-200 transition-colors">
        ← Back to dashboard
      </Link>

      <div className="space-y-3">
        <p className="text-sm uppercase tracking-widest text-amber-400">Labs</p>
        <h1 className="text-4xl font-bold">WSB AI Copilot</h1>
        <p className="text-slate-400 max-w-3xl">
          This page wires up the AI SDK getting-started example (
          <a
            href="https://ai-sdk.dev/docs/getting-started"
            target="_blank"
            rel="noreferrer"
            className="underline decoration-dotted underline-offset-4"
          >
            docs
          </a>
          ) so we can ask questions about hype, sentiment, and alert tiers right inside our Next.js app. Responses stream straight
          from the `/api/chat` route backed by OpenAI&apos;s `gpt-4o-mini` model and always include the live data snapshot shown on this page.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex flex-col gap-4">
          <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 pr-2">
            {messages.length === 0 && (
              <div className="rounded-xl border border-dashed border-slate-800 p-4 text-sm text-slate-400">
                Ask things like &quot;Which tickers hit Tier 1 alerts recently?&quot; or &quot;How does hype compare to unique authors today?&quot;
              </div>
            )}

            {messages.map((message) => (
              <article
                key={message.id}
                className={`rounded-2xl border p-3 text-sm leading-relaxed shadow-sm ${
                  message.role === 'user'
                    ? 'border-amber-500/30 bg-amber-500/5'
                    : 'border-slate-800 bg-slate-900/70'
                }`}
              >
                <header className="text-xs uppercase tracking-wide text-slate-400 mb-1">
                  {message.role === 'assistant' ? 'Radar AI' : 'You'}
                </header>
                {message.parts.map((part, index) => {
                  if (part.type === 'text') {
                    return (
                      <p key={index} className="whitespace-pre-line text-slate-100">
                        {part.text}
                      </p>
                    );
                  }
                  return (
                    <p key={index} className="text-slate-400">
                      [{part.type} content is not rendered]
                    </p>
                  );
                })}
              </article>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about hype, alerts, leaders, or strategy ideas..."
              rows={3}
              className="w-full resize-none rounded-2xl border border-slate-800 bg-slate-950/70 p-3 text-sm text-slate-100 focus:border-amber-400 focus:outline-none"
              disabled={status === 'streaming'}
            />
            <div className="flex items-center gap-3">
              <button
                type="submit"
                className="rounded-xl bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={status === 'streaming' || input.trim().length === 0}
              >
                {status === 'streaming' ? 'Thinking...' : 'Send'}
              </button>
              {status === 'streaming' && (
                <button
                  type="button"
                  onClick={() => stop()}
                  className="text-sm text-slate-400 hover:text-slate-200"
                >
                  Stop response
                </button>
              )}
              <span className="text-xs text-slate-500">Status: {status}</span>
            </div>
          </form>

          {error && <p className="text-sm text-red-400">{error.message}</p>}
        </div>

        <div className="space-y-4">
          <section className="bg-slate-900/20 border border-slate-800 rounded-2xl p-4 text-sm text-slate-300">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-100">Trending snapshot</h2>
                <p className="text-xs text-slate-400">
                  The AI sees the top {Math.min(tickers.length, CONTEXT_TICKER_LIMIT)} tickers from the {analysisWindow.toUpperCase()} window.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {TIMEFRAMES.map((tf) => (
                  <button
                    key={tf}
                    type="button"
                    onClick={() => setAnalysisWindow(tf)}
                    className={`rounded-lg px-3 py-1 text-xs font-semibold transition-colors ${
                      tf === analysisWindow
                        ? 'bg-amber-400 text-slate-950'
                        : 'bg-slate-900 text-slate-200 hover:bg-slate-800'
                    }`}
                  >
                    {tf.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-3 space-y-2">
              {isTrendingLoading && <p className="text-xs text-slate-500">Loading snapshot...</p>}
              {!isTrendingLoading && displayedTickers.length === 0 && (
                <p className="text-xs text-slate-500">No trending data yet. Keep the pipeline running to populate this list.</p>
              )}
              {!isTrendingLoading && displayedTickers.length > 0 && (
                <ul className="space-y-2">
                  {displayedTickers.map((ticker, index) => (
                    <li
                      key={ticker.ticker}
                      className="flex items-start justify-between rounded-xl border border-slate-800/70 bg-slate-950/40 p-3"
                    >
                      <div>
                        <p className="text-sm font-semibold text-slate-100">
                          #{index + 1} {ticker.ticker}
                        </p>
                        <p className="text-xs text-slate-400">
                          Hype {ticker.hype_score.toFixed(1)} · Mentions {ticker.mentions} · Sentiment {(ticker.avg_sentiment * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-right text-xs text-slate-400">
                        <p>Z {ticker.zscore.toFixed(2)}</p>
                        <p>Authors {ticker.unique_authors}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="bg-slate-900/20 border border-slate-800 rounded-2xl p-4 text-sm text-slate-300">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-slate-100">Latest alerts</h2>
              <span className="text-xs text-slate-500">Streaming from /v1/alerts/live</span>
            </div>
            {displayedAlerts.length === 0 ? (
              <p className="mt-2 text-xs text-slate-500">
                Alerts will appear once the detector starts emitting heads-up or actionable events.
              </p>
            ) : (
              <ul className="mt-3 space-y-2">
                {displayedAlerts.map((alert) => (
                  <li key={`${alert.ts}-${alert.ticker}`} className="rounded-xl border border-slate-800/70 bg-slate-950/40 p-3">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-semibold text-slate-100">{alert.ticker}</span>
                      <span>{new Date(alert.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p className="text-xs text-slate-400">
                      {alert.tier.toUpperCase()} · Hype {alert.hype_score.toFixed(1)} · Sentiment {(alert.avg_sentiment * 100).toFixed(0)}% · Authors {alert.unique_authors}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="bg-slate-900/20 border border-slate-800 rounded-2xl p-4 space-y-3 text-sm text-slate-300">
            <div>
              <h2 className="text-base font-semibold text-slate-100">How it works</h2>
              <p className="mt-1 text-slate-400">
                The client uses `useChat` from <code>@ai-sdk/react</code>. The server route enriches each prompt with the trending table and
                alert tape you see above before calling `streamText` with OpenAI&apos;s `gpt-4o-mini`.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Ideas</h3>
              <ul className="list-disc list-inside space-y-1 text-slate-400">
                <li>Ask for summaries of the biggest hype versus sentiment gaps.</li>
                <li>Compare alert tiers to the trending leaderboard.</li>
                <li>Draft talking points for specific tickers based on mentions and z-scores.</li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Configure</h3>
              <ol className="list-decimal list-inside space-y-1 text-slate-400">
                <li>Create `web/.env.local`.</li>
                <li>Add `OPENAI_API_KEY=sk-...`.</li>
                <li>Restart `pnpm dev` so Next.js picks up the key.</li>
              </ol>
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
