import React, { useState } from 'react';
import { askAssistant, AssistantSource } from '../api';

const CROPS = [
  { name: 'Tomato', icon: '🍅' },
  { name: 'Wheat', icon: '🌾' },
  { name: 'Onion', icon: '🧅' },
  { name: 'Potato', icon: '🥔' },
  { name: 'Chilli', icon: '🌶️' },
  { name: 'Rice', icon: '🌾' },
  { name: 'Maize', icon: '🌽' },
  { name: 'Marigold', icon: '🌼' },
  { name: 'Rose', icon: '🌹' },
  { name: 'Sugarcane', icon: '🎋' },
  { name: 'Cotton', icon: '🧶' },
  { name: 'Mustard', icon: '🌱' },
];

// Strip basic markdown markers so the LLM answer reads cleanly.
function clean(text: string): string {
  return text.replace(/\*\*/g, '').replace(/^#+\s*/gm, '');
}

interface Advisory {
  crop: string;
  answer: string;
  mode: string;
  sources: AssistantSource[];
}

export default function CropAdvisory() {
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadCrop = async (crop: string) => {
    setSelected(crop);
    setAdvisory(null);
    setError(null);
    setLoading(true);
    try {
      const res = await askAssistant(
        `Give a practical crop advisory for ${crop} farming in India. Cover: best ` +
          `sowing season, fertilizer schedule with NPK, irrigation, and the common ` +
          `pests/diseases with their control. Keep it short and simple for a farmer.`,
      );
      setAdvisory({ crop, answer: clean(res.answer), mode: res.mode, sources: res.sources });
    } catch (e) {
      setError('Could not load advisory. Is the backend running on :8000?');
    } finally {
      setLoading(false);
    }
  };

  const back = () => {
    setSelected(null);
    setAdvisory(null);
    setError(null);
  };

  // Detail view for a selected crop
  if (selected) {
    return (
      <div className="p-4">
        <button onClick={back} className="text-sm text-brand mb-3 underline">
          ← All crops
        </button>
        <h1 className="text-2xl font-bold mb-4 text-brand flex items-center gap-2">
          <span>{CROPS.find((c) => c.name === selected)?.icon}</span> {selected}
        </h1>

        {loading && (
          <div className="bg-white p-4 rounded-xl shadow-sm text-gray-500">
            Preparing {selected} advisory… 🌱
          </div>
        )}
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>
        )}
        {advisory && (
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <span
              className={`inline-block text-[10px] px-2 py-0.5 rounded-full mb-3 ${
                advisory.mode === 'web'
                  ? 'bg-blue-100 text-blue-700'
                  : advisory.mode === 'knowledge_base'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {advisory.mode === 'web'
                ? '🌐 Web'
                : advisory.mode === 'knowledge_base'
                ? '📚 Knowledge base'
                : '📄 Offline'}
            </span>
            <p className="text-gray-800 whitespace-pre-line leading-relaxed">
              {advisory.answer}
            </p>
            {advisory.sources?.length > 0 && (
              <div className="mt-4 pt-3 border-t flex flex-wrap gap-1">
                {advisory.sources.slice(0, 4).map((s, i) =>
                  s.kind === 'web' && s.url ? (
                    <a
                      key={i}
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full hover:underline max-w-[160px] truncate"
                    >
                      {s.title || s.url}
                    </a>
                  ) : (
                    <span
                      key={i}
                      className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full"
                    >
                      {s.title}
                    </span>
                  ),
                )}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Crop grid
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-1 text-brand">Crop Advisory</h1>
      <p className="text-[#78716C] mb-6">Tap a crop for season, fertilizer, irrigation & pest advice.</p>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {CROPS.map((crop) => (
          <button
            key={crop.name}
            onClick={() => loadCrop(crop.name)}
            className="bg-white p-4 rounded-xl shadow border border-gray-100 flex flex-col items-center hover:shadow-lg hover:border-brand transition"
          >
            <div className="h-16 w-16 bg-gray-50 rounded-full mb-3 flex items-center justify-center text-3xl">
              {crop.icon}
            </div>
            <span className="font-semibold text-ink">{crop.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
