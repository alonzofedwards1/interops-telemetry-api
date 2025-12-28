import { useEffect, useMemo, useState } from 'react';
import { get } from '../api/client';

export type TelemetryEvent = {
  time: string;
  source: string;
  protocol: string;
  outcome: string;
  correlation_id?: string;
};

interface Props {
  correlationId?: string | null;
}

const REFRESH_MS = 15_000;

export default function TelemetryTable({ correlationId }: Props) {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const filteredEvents = useMemo(() => {
    if (!correlationId) return events;
    return events.filter((event) => event.correlation_id === correlationId);
  }, [events, correlationId]);

  const loadEvents = async (signal?: AbortSignal) => {
    setLoading(true);
    try {
      const data = await get<TelemetryEvent[]>('/telemetry/events', signal);
      setEvents(data);
      setError(null);
    } catch (err) {
      if (signal?.aborted) return;
      setError(err instanceof Error ? err.message : 'Unable to load telemetry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    loadEvents(controller.signal);

    if (!autoRefresh) return () => controller.abort();

    const interval = setInterval(() => loadEvents(controller.signal), REFRESH_MS);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh]);

  return (
    <section className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 shadow-md">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-300 uppercase tracking-wide">Telemetry</p>
          <h2 className="text-lg font-semibold text-slate-100">System Events</h2>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            <span className="text-slate-200">Auto-refresh</span>
          </label>
          <button
            onClick={() => loadEvents()}
            className="px-3 py-1 rounded bg-slate-700 border border-slate-600 text-slate-100 hover:bg-slate-600"
          >
            Refresh
          </button>
        </div>
      </header>

      {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      {loading && <p className="mt-3 text-sm text-slate-400">Fetching latest telemetry…</p>}

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-slate-900 text-slate-300">
            <tr>
              <th className="px-3 py-2 font-semibold">Time</th>
              <th className="px-3 py-2 font-semibold">Source</th>
              <th className="px-3 py-2 font-semibold">Protocol</th>
              <th className="px-3 py-2 font-semibold">Outcome</th>
              <th className="px-3 py-2 font-semibold">Correlation ID</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.map((event, idx) => (
              <tr key={`${event.time}-${idx}`} className="border-b border-slate-700 last:border-none">
                <td className="px-3 py-2 text-slate-100 whitespace-nowrap">
                  {new Date(event.time).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-slate-200">{event.source}</td>
                <td className="px-3 py-2 text-slate-200">{event.protocol}</td>
                <td className="px-3 py-2 text-slate-200">{event.outcome}</td>
                <td className="px-3 py-2 text-slate-400 font-mono">{event.correlation_id ?? '—'}</td>
              </tr>
            ))}
            {filteredEvents.length === 0 && !loading && (
              <tr>
                <td className="px-3 py-3 text-slate-400" colSpan={5}>
                  No telemetry events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
