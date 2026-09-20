import React from 'react';
import { Settings, Key, Cloud, Database } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings & Cloud Configuration</h1>
        <p className="text-sm text-slate-500 mt-1">Configure OpenAI, Azure OpenAI, Azure Blob Storage, and Database settings.</p>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-6">
        <div>
          <h3 className="text-md font-semibold text-slate-800 flex items-center space-x-2">
            <Key className="w-5 h-5 text-indigo-600" />
            <span>AI / LLM Service Configuration</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">LabTrace falls back to deterministic local AI analysis if API keys are empty.</p>
        </div>

        <div className="grid grid-cols-1 gap-4 max-w-xl">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">OpenAI API Key</label>
            <input
              type="password"
              placeholder="sk-..."
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Azure OpenAI Endpoint</label>
            <input
              type="text"
              placeholder="https://your-resource.openai.azure.com/"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
