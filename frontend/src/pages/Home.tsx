import React from 'react';
import { Link } from 'react-router-dom';

const cards = [
  { to: '/ask', icon: '🌾', label: 'Ask AI', border: 'border-green-500' },
  { to: '/crops', icon: '🌱', label: 'Crops', border: 'border-emerald-500' },
  { to: '/diagnose', icon: '📷', label: 'Diagnose', border: 'border-amber-500' },
  { to: '/faq', icon: '❓', label: 'FAQ', border: 'border-purple-500' },
];

export default function Home() {
  return (
    <div className="p-4 flex flex-col items-center">
      <h1 className="text-2xl font-bold mb-6 text-ink">Sawaal poochho</h1>

      <Link
        to="/ask"
        className="bg-brand text-white p-8 rounded-full shadow-lg flex flex-col items-center justify-center transform hover:scale-105 transition"
      >
        <span className="text-4xl mb-2">🌾</span>
        <span className="text-lg font-semibold">Ask AI</span>
      </Link>

      <div className="grid grid-cols-2 gap-4 mt-10 w-full px-2">
        {cards.map((c) => (
          <Link
            key={c.to}
            to={c.to}
            className={`bg-white p-6 shadow-md rounded-xl text-center border-l-4 ${c.border} hover:shadow-lg transition`}
          >
            <div className="text-3xl mb-2">{c.icon}</div>
            <div className="font-semibold text-ink">{c.label}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
