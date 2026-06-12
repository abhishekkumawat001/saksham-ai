import React, { useEffect, useState } from 'react';
import { listFaqs, searchFaqs, FaqItem, SearchResult } from '../api';

export default function FAQ() {
  const [all, setAll] = useState<FaqItem[]>([]);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the full FAQ list on first render.
  useEffect(() => {
    listFaqs('hi')
      .then(setAll)
      .catch((e) => setError(String(e)));
  }, []);

  const runSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await searchFaqs(query, 3);
      setResults(res.results);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const clear = () => {
    setQuery('');
    setResults(null);
    setError(null);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-ink">Aam Sawaal (FAQ)</h1>

      <form onSubmit={runSearch} className="flex gap-2 mb-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Koi sawaal type karein… (e.g. tamatar me khaad)"
          className="flex-1 p-3 border rounded-full focus:outline-none focus:border-brand"
        />
        <button
          type="submit"
          className="bg-brand text-white px-5 rounded-full font-semibold disabled:opacity-60"
          disabled={loading}
        >
          {loading ? '…' : 'Search'}
        </button>
      </form>

      {results !== null && (
        <button onClick={clear} className="text-sm text-brand mb-4 underline">
          ← Back to all FAQs
        </button>
      )}

      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4 text-sm">
          {error} — is the backend running on :8000?
        </div>
      )}

      {/* Search results, scored by the real semantic index */}
      {results !== null ? (
        <div className="space-y-4">
          {results.length === 0 && <p className="text-gray-500">No results.</p>}
          {results.map((r) => (
            <div
              key={r.id}
              className={`bg-white p-4 rounded-lg shadow-sm border ${
                r.matched ? 'border-green-300' : 'border-gray-100'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase tracking-wide text-gray-400">
                  {r.category}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    r.matched
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {r.matched ? 'match' : 'low'} · {r.score.toFixed(2)}
                </span>
              </div>
              <h3 className="font-bold text-brand mb-1">{r.question}</h3>
              <p className="text-gray-700 whitespace-pre-line">{r.answer}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {all.length === 0 && !error && (
            <p className="text-gray-400">Loading FAQs…</p>
          )}
          {all.map((f) => (
            <div
              key={f.id}
              className="bg-white p-4 rounded-lg shadow-sm border border-gray-100"
            >
              <h3 className="font-bold text-brand mb-1">{f.question}</h3>
              <p className="text-gray-700 whitespace-pre-line">{f.answer}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
