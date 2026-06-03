import React from 'react';

export default function Home() {
  return (
    <div className="p-4 flex flex-col items-center">
      {/* Hero section with large Voice CTA as requested */}
      <h1 className="text-2xl font-bold mb-6 text-[#1C1917]">Sawaal poochho</h1>
      
      <button className="bg-[#1B6B3A] text-white p-8 rounded-full shadow-lg flex flex-col items-center justify-center transform hover:scale-105 transition">
        <span className="text-4xl mb-2">🎤</span>
        <span className="text-lg font-semibold">Voice Start</span>
      </button>

      <div className="grid grid-cols-2 gap-4 mt-10 w-full px-2">
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-green-500">
          <div className="text-3xl mb-2">🌱</div>
          <div className="font-semibold text-[#1C1917]">Crops</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-blue-500">
          <div className="text-3xl mb-2">💬</div>
          <div className="font-semibold text-[#1C1917]">Chat</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-amber-500">
          <div className="text-3xl mb-2">📷</div>
          <div className="font-semibold text-[#1C1917]">Diagnose</div>
        </div>
        <div className="bg-white p-6 shadow-md rounded-xl text-center border-l-4 border-purple-500">
          <div className="text-3xl mb-2">❓</div>
          <div className="font-semibold text-[#1C1917]">FAQ</div>
        </div>
      </div>
    </div>
  );
}
