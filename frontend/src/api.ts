// Thin client for the KisanSaathi backend.
// In dev, requests go to /api/* and Vite proxies them to FastAPI (see
// vite.config.ts). Override with VITE_API_BASE for a deployed backend.
const BASE = import.meta.env.VITE_API_BASE ?? '';

export interface FaqItem {
  id: string;
  category: string;
  question: string;
  answer: string;
}

export interface SearchResult extends FaqItem {
  score: number;
  matched: boolean;
}

export interface SearchResponse {
  query: string;
  language: string;
  results: SearchResult[];
}

export interface AskResponse {
  reply: string;
  resolved: boolean;
  matched_faq_id: string | null;
  score: number;
  language: string;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function listFaqs(lang = 'hi'): Promise<FaqItem[]> {
  return http<FaqItem[]>(`/api/v1/faqs/?lang=${encodeURIComponent(lang)}`);
}

export function searchFaqs(q: string, topK = 3): Promise<SearchResponse> {
  return http<SearchResponse>(
    `/api/v1/faqs/search?q=${encodeURIComponent(q)}&top_k=${topK}`,
  );
}

export function ask(message: string): Promise<AskResponse> {
  return http<AskResponse>('/api/v1/faqs/ask', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

// --- RAG assistant (knowledge base + Groq LLM + web search) ------------
export interface AssistantSource {
  title: string;
  source: string;
  score: number;
  url: string;
  kind: 'kb' | 'web';
}

export interface AssistantAnswer {
  answer: string;
  used_llm: boolean;
  language: string;
  mode: 'knowledge_base' | 'web' | 'extractive';
  sources: AssistantSource[];
}

export interface AssistantStatus {
  knowledge_chunks: number;
  llm_available: boolean;
  model: string | null;
  web_search: boolean;
}

export function assistantStatus(): Promise<AssistantStatus> {
  return http<AssistantStatus>('/api/v1/assistant/status');
}

export function askAssistant(
  message: string,
  opts?: { topK?: number; webSearch?: boolean },
): Promise<AssistantAnswer> {
  return http<AssistantAnswer>('/api/v1/assistant/ask', {
    method: 'POST',
    body: JSON.stringify({
      message,
      top_k: opts?.topK,
      web_search: opts?.webSearch,
    }),
  });
}
