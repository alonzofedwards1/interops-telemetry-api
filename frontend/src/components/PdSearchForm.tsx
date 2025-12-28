import { FormEvent, useState } from 'react';
import { post } from '../api/client';

export type PdSearchInput = {
  firstName: string;
  lastName: string;
  dob: string;
};

export type PdSearchResponse = {
  correlation_id: string;
};

interface Props {
  onSearchComplete: (correlationId: string, input: PdSearchInput) => void;
}

export default function PdSearchForm({ onSearchComplete }: Props) {
  const [form, setForm] = useState<PdSearchInput>({ firstName: '', lastName: '', dob: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [correlationId, setCorrelationId] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    if (!form.firstName || !form.lastName || !form.dob) {
      setError('All fields are required to trigger a search request.');
      return;
    }

    setLoading(true);
    try {
      const response = await post<PdSearchResponse>('/pd/search', form);
      setCorrelationId(response.correlation_id);
      onSearchComplete(response.correlation_id, form);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit search request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 shadow-md">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-300 uppercase tracking-wide">Workflow trigger</p>
          <h2 className="text-lg font-semibold text-slate-100">Patient Discovery Search</h2>
        </div>
        {correlationId && (
          <span className="text-xs px-2 py-1 bg-slate-700 border border-slate-600 rounded text-slate-200 font-mono">
            ID: {correlationId}
          </span>
        )}
      </header>

      <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="flex flex-col text-sm text-slate-200">
            First Name
            <input
              className="mt-1 rounded border border-slate-600 bg-slate-900 p-2 text-slate-100"
              type="text"
              value={form.firstName}
              onChange={(e) => setForm((prev) => ({ ...prev, firstName: e.target.value }))}
              placeholder="e.g. Ada"
              required
            />
          </label>
          <label className="flex flex-col text-sm text-slate-200">
            Last Name
            <input
              className="mt-1 rounded border border-slate-600 bg-slate-900 p-2 text-slate-100"
              type="text"
              value={form.lastName}
              onChange={(e) => setForm((prev) => ({ ...prev, lastName: e.target.value }))}
              placeholder="e.g. Lovelace"
              required
            />
          </label>
        </div>
        <label className="flex flex-col text-sm text-slate-200">
          Date of Birth
          <input
            className="mt-1 rounded border border-slate-600 bg-slate-900 p-2 text-slate-100"
            type="date"
            value={form.dob}
            onChange={(e) => setForm((prev) => ({ ...prev, dob: e.target.value }))}
            required
          />
        </label>

        {error && <p className="text-sm text-red-300">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto px-4 py-2 rounded bg-sky-600 hover:bg-sky-500 text-sm font-semibold text-white transition"
        >
          {loading ? 'Submitting…' : 'Trigger search request'}
        </button>
      </form>

      {correlationId && (
        <div className="mt-4 text-sm text-slate-200">
          Workflow triggered. Correlation ID: <span className="font-mono text-sky-200">{correlationId}</span>
        </div>
      )}
    </section>
  );
}
