import React, { useEffect, useRef, useState } from 'react';
import {
  askAssistant,
  assistantStatus,
  AssistantSource,
  AssistantStatus,
} from '../api';

interface Msg {
  sender: 'bot' | 'user';
  text: string;
  usedLlm?: boolean;
  mode?: 'knowledge_base' | 'web' | 'extractive';
  sources?: AssistantSource[];
}

const MODE_BADGE: Record<string, { label: string; cls: string }> = {
  knowledge_base: { label: '📚 Knowledge base', cls: 'bg-green-100 text-green-700' },
  web: { label: '🌐 Web search', cls: 'bg-blue-100 text-blue-700' },
  extractive: { label: '📄 Extractive (no LLM)', cls: 'bg-amber-100 text-amber-700' },
};

const SUGGESTIONS = [
  'Which fertilizer for tomato at flowering?',
  'Best wheat variety for late sowing?',
  'How to do seed treatment before sowing?',
  'How to grow marigold?',
];

export default function Assistant() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      sender: 'bot',
      text: 'Namaste! Ask me anything about fertilizers, seeds, wheat, vegetables or flowers. 🌾',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  const [webSearch, setWebSearch] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    assistantStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (q?: string) => {
    const text = (q ?? input).trim();
    if (!text || sending) return;
    setMessages((m) => [...m, { sender: 'user', text }]);
    setInput('');
    setSending(true);
    try {
      const res = await askAssistant(text, { webSearch });
      setMessages((m) => [
        ...m,
        {
          sender: 'bot',
          text: res.answer,
          usedLlm: res.used_llm,
          mode: res.mode,
          sources: res.sources,
        },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          sender: 'bot',
          text: 'Server is warming up — this can take 30–60 seconds on first use. Please try again in a moment. 🌱',
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="p-4 bg-brand text-white flex items-start justify-between gap-2">
        <div>
          <h1 className="text-lg font-bold">Ask AI 🌾</h1>
          <p className="text-xs opacity-80">
            {status
              ? `${status.knowledge_chunks > 0 ? `${status.knowledge_chunks} KB chunks` : 'KB loading…'} · ${
                  status.llm_available ? `LLM: ${status.model}` : 'LLM off (extractive)'
                }`
              : 'connecting…'}
          </p>
        </div>
        {status?.llm_available && (
          <button
            onClick={() => setWebSearch((v) => !v)}
            title="Toggle web search for questions not in the knowledge base"
            className={`shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full border transition ${
              webSearch
                ? 'bg-white text-brand border-white'
                : 'bg-transparent text-white/80 border-white/40'
            }`}
          >
            🌐 Web: {webSearch ? 'ON' : 'OFF'}
          </button>
        )}
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map((m, i) => (
          <div key={i} className="space-y-1">
            <div
              className={`p-3 rounded-2xl max-w-[88%] whitespace-pre-line ${
                m.sender === 'bot'
                  ? 'mr-auto bg-white text-gray-800'
                  : 'bg-green-100 ml-auto text-green-900'
              }`}
            >
              {m.text}
            </div>
            {m.sender === 'bot' && m.mode && (
              <div className="mr-auto max-w-[88%] flex flex-wrap items-center gap-1 pl-1">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full ${
                    MODE_BADGE[m.mode]?.cls ?? 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {MODE_BADGE[m.mode]?.label ?? m.mode}
                </span>
                {m.sources?.slice(0, 4).map((s, j) =>
                  s.kind === 'web' && s.url ? (
                    <a
                      key={j}
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full hover:underline max-w-[160px] truncate"
                      title={s.url}
                    >
                      {s.title || s.url}
                    </a>
                  ) : (
                    <span
                      key={j}
                      className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full"
                      title={s.source}
                    >
                      {s.title} · {s.score.toFixed(2)}
                    </span>
                  )
                )}
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="mr-auto bg-white text-gray-400 p-3 rounded-2xl">thinking…</div>
        )}
        <div ref={endRef} />
      </div>

      {messages.length <= 1 && (
        <div className="px-3 pb-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:border-brand"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="p-3 bg-white border-t flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about fertilizers, seeds, crops…"
          className="flex-1 p-3 border rounded-full focus:outline-none focus:border-brand"
        />
        <button
          onClick={() => send()}
          disabled={sending}
          className="bg-brand text-white w-12 h-12 rounded-full text-xl leading-none disabled:opacity-60"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
