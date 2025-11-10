export default function AlertsPage() {
  return (
    <section className="space-y-3">
      <h1 className="text-3xl font-semibold">Live Alerts</h1>
      <p className="text-slate-400 text-sm">
        Wire this view to the /v1/alerts/live SSE endpoint to stream actionable alerts.
      </p>
    </section>
  );
}
