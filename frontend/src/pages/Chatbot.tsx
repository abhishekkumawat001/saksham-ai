import React, { useEffect, useRef, useState } from 'react';
import { ask } from '../api';

interface Msg {
  sender: 'bot' | 'user';
  text: string;
  escalated?: boolean;
}

export default function Chatbot() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      sender: 'bot',
      text: 'Namaste! Main KisanSaathi hoon. Kheti se juda koi bhi sawaal poochhein. 🌱',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setMessages((m) => [...m, { sender: 'user', text }]);
    setInput('');
    setSending(true);
    try {
      const res = await ask(text);
      setMessages((m) => [
        ...m,
        { sender: 'bot', text: res.reply, escalated: !res.resolved },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          sender: 'bot',
          text: 'Server se baat nahi ho payi. Kya backend :8000 par chal raha hai?',
          escalated: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="p-4 bg-brand text-white">
        <h1 className="text-lg font-bold">KisanSaathi Chat</h1>
        <p className="text-xs opacity-80">FAQ engine · Hindi & English</p>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-3 rounded-2xl max-w-[85%] whitespace-pre-line ${
              m.sender === 'bot'
                ? `mr-auto ${
                    m.escalated
                      ? 'bg-amber-50 border border-amber-200 text-amber-900'
                      : 'bg-white text-gray-800'
                  }`
                : 'bg-green-100 ml-auto text-green-900'
            }`}
          >
            {m.text}
          </div>
        ))}
        {sending && (
          <div className="mr-auto bg-white text-gray-400 p-3 rounded-2xl">…</div>
        )}
        <div ref={endRef} />
      </div>

      <div className="p-3 bg-white border-t flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Apna sawaal type karein…"
          className="flex-1 p-3 border rounded-full focus:outline-none focus:border-brand"
        />
        <button
          onClick={handleSend}
          disabled={sending}
          className="bg-brand text-white w-12 h-12 rounded-full text-xl leading-none disabled:opacity-60"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
