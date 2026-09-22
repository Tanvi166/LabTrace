import React, { useEffect, useState } from 'react';
import { Loader2, MessageSquare, Send } from 'lucide-react';
import {
  experimentApi,
  ChatResponse,
} from '../services/api';

export const RagPage: React.FC = () => {
  const [provider, setProvider] = useState('loading');
  const [chunkCount, setChunkCount] = useState<number | null>(null);

  const [chatQuestion, setChatQuestion] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [chatResponse, setChatResponse] =
    useState<ChatResponse | null>(null);

  useEffect(() => {
    experimentApi
      .getRagStatus()
      .then((s) => {
        console.log('RAG STATUS:', s);

        setProvider(
          s.connected
            ? s.provider
            : `${s.provider} (not connected)`
        );

        setChunkCount(
          typeof s.chunks === 'number' ? s.chunks : null
        );
      })
      .catch((err) => {
        console.error('RAG STATUS ERROR:', err);
        console.error('Response:', err?.response);
        console.error('Data:', err?.response?.data);

        setProvider('unavailable');
      });
  }, []);

  const askLabTrace = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!chatQuestion.trim()) return;

    setChatLoading(true);
    setChatError(null);

    try {
      const response = await experimentApi.chat(
        chatQuestion.trim()
      );

      console.log('LABTRACE CHAT RESPONSE:', response);

      setChatResponse(response);
    } catch (err: any) {
      console.error('LABTRACE CHAT ERROR:', err);
      console.error('Response:', err?.response);
      console.error('Data:', err?.response?.data);

      setChatResponse(null);

      setChatError(
        err?.response?.data?.detail ||
        err?.message ||
        'LabTrace RAG request failed'
      );
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="space-y-6">

      {/* ASK LABTRACE */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">

        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-indigo-600" />

          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Ask LabTrace
            </h2>

            <p className="text-sm text-slate-500">
              Ask questions using the LabTrace knowledge base.
            </p>
          </div>
        </div>

        <form onSubmit={askLabTrace}>
          <div className="relative">

            <MessageSquare
              className="w-5 h-5 absolute left-3 top-3 text-slate-400"
            />

            <input
              value={chatQuestion}
              onChange={(e) =>
                setChatQuestion(e.target.value)
              }
              type="text"
              placeholder="Ask something about your research..."
              className="w-full pl-10 pr-12 py-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm"
            />

            <button
              type="submit"
              disabled={
                chatLoading ||
                !chatQuestion.trim()
              }
              className="absolute right-2 top-2 p-1.5 bg-indigo-600 text-white rounded-md disabled:bg-indigo-300"
            >
              {chatLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>

          </div>
        </form>

        {chatError && (
          <p className="text-sm text-red-600">
            {chatError}
          </p>
        )}

        {chatResponse && (
          <div className="space-y-4">

            {/* ANSWER */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">

              <h3 className="font-semibold text-slate-800 mb-2">
                LabTrace Answer
              </h3>

              <p className="text-sm text-slate-700 whitespace-pre-wrap">
                {chatResponse.answer}
              </p>

            </div>

            {/* SOURCES */}
            {chatResponse.sources.length > 0 && (
              <div>

                <h3 className="text-sm font-semibold text-slate-800 mb-2">
                  Sources
                </h3>

                <div className="space-y-2">

                  {chatResponse.sources.map((source) => (
                    <div
                      key={source.chunk_id}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-lg"
                    >

                      <div className="flex justify-between gap-3">

                        <span className="text-sm font-medium text-slate-700">
                          {source.title}
                        </span>

                        <span className="text-xs text-indigo-700">
                          Score {source.score.toFixed(3)}
                        </span>

                      </div>

                      <p className="text-xs text-slate-500 mt-1">
                        Chunk: {source.chunk_id}
                      </p>

                    </div>
                  ))}

                </div>
              </div>
            )}

          </div>
        )}

      </div>

      {/* RAG STATUS */}
      <div className="bg-white p-6 rounded-xl border border-slate-200">

        <div className="flex items-center justify-between">

          <div>
            <h3 className="text-sm font-semibold text-slate-800">
              Knowledge Base
            </h3>

            <p className="text-xs text-slate-500 mt-1">
              Provider: {provider}
            </p>
          </div>

          {chunkCount !== null && (
            <div className="text-right">
              <p className="text-lg font-semibold text-indigo-600">
                {chunkCount}
              </p>

              <p className="text-xs text-slate-500">
                chunks
              </p>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};