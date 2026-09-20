import React, { useEffect, useState } from 'react';
import { BookOpen, Search, Loader2 } from 'lucide-react';
import { experimentApi, KnowledgeResult } from '../services/api';

export const RagPage: React.FC = () => {
  const [query, setQuery] = useState(''); const [results, setResults] = useState<KnowledgeResult[]>([]); const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null); const [provider, setProvider] = useState('loading'); const [chunkCount, setChunkCount] = useState<number | null>(null); const [searched, setSearched] = useState(false);
  useEffect(() => { experimentApi.getRagStatus().then(s => { setProvider(s.connected ? s.provider : `${s.provider} (not connected)`); setChunkCount(typeof s.chunks === 'number' ? s.chunks : null); }).catch(() => setProvider('unavailable')); }, []);
  const search = async (event: React.FormEvent) => { event.preventDefault(); if (!query.trim()) return; setLoading(true); setError(null); setSearched(true); try { setResults(await experimentApi.searchKnowledge(query)); } catch (err: any) { setResults([]); setError(err.response?.data?.detail || 'Search failed'); } finally { setLoading(false); } };
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">RAG Knowledge Engine</h1>
        <p className="text-sm text-slate-500 mt-1">Search NeurIPS, ACM, PyTorch & TensorFlow reproducibility standards.</p>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
        <p className="text-xs text-slate-500">Knowledge provider: {provider}. Knowledge document ingestion is available to administrators only.</p>
        <form onSubmit={search}>
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-3 text-slate-400" />
          <input value={query} onChange={e => setQuery(e.target.value)}
            type="text"
            placeholder="Search reproducibility standards e.g. 'how to fix non-deterministic CUDA operations'..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
          />
        </div>
        <button disabled={loading} className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm disabled:bg-indigo-400">{loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search knowledge'}</button>
        </form>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {searched && !loading && !error && results.length === 0 && <p className="text-sm text-slate-500">{chunkCount === 0 ? 'Knowledge base is empty. An administrator must ingest knowledge documents before searches can return results.' : 'No matching knowledge found.'}</p>}
        <div className="space-y-3">{results.map(result => <article key={result.chunk_id} className="p-4 bg-slate-50 border border-slate-200 rounded-lg"><div className="flex justify-between gap-3"><h3 className="font-semibold text-slate-800">{result.title}</h3><span className="text-xs text-indigo-700">Score {result.score.toFixed(3)}</span></div><p className="text-sm text-slate-600 mt-2">{result.content}</p><p className="text-xs text-slate-500 mt-2">Source: {result.source} · Chunk {result.chunk_id}</p></article>)}</div>
      </div>
    </div>
  );
};
