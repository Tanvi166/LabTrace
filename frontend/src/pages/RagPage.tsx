import React, { useEffect, useState, useRef } from 'react';
import { Loader2, Send, Download, Bot, AlertCircle } from 'lucide-react';
import { experimentApi, ChatResponse, Experiment } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: { title: string; chunk_id: string; score: number }[];
}

export const RagPage: React.FC = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch experiments for dropdown
    const fetchExps = async () => {
      try {
        const res = await experimentApi.getExperiments({ page: 1, page_size: 100 });
        if (res.items && res.items.length > 0) {
          setExperiments(res.items);
          setSelectedExpId(res.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load experiments', err);
      }
    };
    fetchExps();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // If an experiment is selected, we can optionally append it to the query context for the backend
      const expTitle = experiments.find(e => e.id === selectedExpId)?.title || 'general context';
      const augmentedQuery = `Regarding experiment ${expTitle}: ${userMessage}`;
      
      const response = await experimentApi.chat(augmentedQuery);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources
        }
      ]);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to get a response');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-full pb-6">
      <div className="glass-panel p-6 flex flex-col h-[calc(100vh-120px)] relative">
        
        {/* Header */}
        <div className="flex justify-between items-start mb-6 shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">Ask about this experiment</h2>
            <p className="text-sm text-slate-400">Get AI answers grounded in your experiment's content.</p>
          </div>
          <button className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 transition-colors border border-white/10">
            <Download className="w-5 h-5" />
          </button>
        </div>

        {/* Experiment Selector */}
        <div className="mb-6 shrink-0 relative">
          <select
            value={selectedExpId}
            onChange={(e) => setSelectedExpId(e.target.value)}
            className="w-full bg-slate-800/60 border border-slate-700/50 text-slate-200 text-sm rounded-xl px-4 py-3.5 focus:ring-2 focus:ring-brand-500 focus:outline-none appearance-none cursor-pointer pr-10 shadow-inner"
          >
            {experiments.map(exp => (
              <option key={exp.id} value={exp.id}>
                {exp.title} {exp.description ? `- ${exp.description}` : ''}
              </option>
            ))}
            {experiments.length === 0 && (
              <option value="">No experiments found...</option>
            )}
          </select>
          <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
            <svg width="12" height="8" viewBox="0 0 12 8" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M1 1.5L6 6.5L11 1.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto pr-4 space-y-6 mb-6 custom-scrollbar">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              
              {/* AI Message */}
              {msg.role === 'assistant' && (
                <div className="flex max-w-[85%] items-start space-x-4">
                  <div className="flex-shrink-0 w-11 h-11 rounded-full bg-slate-800/80 border border-slate-600/50 flex items-center justify-center text-brand-400 mt-1 shadow-lg shadow-black/20">
                    <Bot className="w-6 h-6" />
                  </div>
                  <div className="bg-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-3xl rounded-tl-sm px-6 py-5 text-slate-300 text-sm leading-relaxed shadow-md">
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-5 pt-4 border-t border-slate-700/50">
                        <h4 className="text-xs font-semibold text-slate-400 mb-2 tracking-wider">Sources:</h4>
                        <ol className="list-decimal list-inside space-y-1.5 text-xs">
                          {msg.sources.map((src, i) => (
                            <li key={i} className="text-brand-400 hover:text-brand-300 cursor-pointer transition-colors truncate">
                              {src.title} <span className="text-slate-500 ml-1 opacity-70">(Chunk {src.chunk_id})</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* User Message */}
              {msg.role === 'user' && (
                <div className="max-w-[75%] bg-gradient-to-br from-brand-500 to-blue-600 text-white rounded-3xl rounded-tr-sm px-6 py-4 text-sm leading-relaxed shadow-lg shadow-brand-500/20">
                  {msg.content}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-start space-x-4">
               <div className="flex-shrink-0 w-11 h-11 rounded-full bg-slate-800/80 border border-slate-600/50 flex items-center justify-center text-brand-400 mt-1 shadow-lg shadow-black/20">
                 <Bot className="w-6 h-6" />
               </div>
               <div className="bg-slate-800/40 border border-slate-700/50 rounded-3xl rounded-tl-sm px-6 py-5 text-slate-300 text-sm flex items-center space-x-2">
                 <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                 <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                 <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
               </div>
            </div>
          )}

          {error && (
            <div className="flex items-start space-x-4">
               <div className="flex-shrink-0 w-11 h-11 rounded-full bg-red-900/50 border border-red-500/30 flex items-center justify-center text-red-400 mt-1">
                 <AlertCircle className="w-6 h-6" />
               </div>
               <div className="bg-red-900/20 border border-red-500/30 rounded-3xl rounded-tl-sm px-6 py-5 text-red-200 text-sm">
                 {error}
               </div>
            </div>
          )}
          
          <div ref={messagesEndRef} className="h-4" />
        </div>

        {/* Input Area */}
        <form onSubmit={handleSubmit} className="relative mt-auto shrink-0 flex items-center">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question about this experiment..."
            className="w-full bg-slate-900/60 backdrop-blur-md border border-slate-700 text-white text-sm rounded-full pl-6 pr-16 py-4 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-all placeholder:text-slate-500 shadow-inner"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !inputValue.trim()}
            className="absolute right-2 top-2 bottom-2 aspect-square rounded-full bg-brand-500 hover:bg-brand-400 disabled:bg-slate-700/50 disabled:text-slate-500 flex items-center justify-center text-white transition-colors"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-4 h-4 ml-[-2px]" />}
          </button>
        </form>
        
      </div>
    </div>
  );
};