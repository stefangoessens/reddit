import { AlertsFeed } from '@/components/AlertsFeed';
import { Heatboard } from '@/components/Heatboard';
import { useTrending } from '@/hooks/useTrending';

export default function HomePage() {
  const { tickers, isLoading, isError } = useTrending();
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-widest text-amber-400">Now</p>
        <h1 className="text-4xl font-bold mt-2">WallStreetBets Hype Radar</h1>
        <p className="text-slate-400 mt-2">
          {isLoading && 'Loading live hype…'}
          {isError && 'Unable to load data right now. Check API connectivity.'}
          {!isLoading && !isError && 'Live hype across WallStreetBets tickers.'}
        </p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Heatboard data={tickers} />
        </div>
        <div className="space-y-3">
          <h2 className="text-xl font-semibold">Live Alerts</h2>
          <AlertsFeed />
        </div>
      </div>
    </section>
  );
}
