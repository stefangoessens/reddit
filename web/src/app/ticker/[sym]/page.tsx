interface PageProps {
  params: { sym: string };
}

export default function TickerPage({ params }: PageProps) {
  return (
    <section className="space-y-3">
      <h1 className="text-3xl font-semibold">{params.sym.toUpperCase()}</h1>
      <p className="text-slate-400 text-sm">
        This drilldown will show mention counts, sentiment, and price overlays.
      </p>
    </section>
  );
}
