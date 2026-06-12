"""Central PoC configuration, env-driven.

Only the WhatsApp FAQ PoC settings live here. Everything reads from
environment variables so nothing secret is committed. See .env.example.
"""
import os
from functools import lru_cache


def _load_dotenv() -> None:
    """Load backend/.env into os.environ if present (no extra dependency).

    Existing environment variables always win, so an explicitly exported value
    overrides the file. Lines are KEY=VALUE; blanks and #comments are ignored.
    """
    # config.py -> core -> app -> backend/.env
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


_load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        # --- Embedding backend ---------------------------------------
        # "openai"  -> text-embedding-3-small (production, needs key)
        # "local"   -> offline TF-IDF fallback (demo / tests, no key)
        # "auto"    -> openai if OPENAI_API_KEY present, else local
        self.embedding_backend = os.getenv("EMBEDDING_BACKEND", "auto").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )

        # --- FAQ matching --------------------------------------------
        # Cosine cutoff. Defaults differ by backend because TF-IDF cosine
        # and dense-embedding cosine are not on the same scale.
        self._threshold_override = os.getenv("FAQ_MATCH_THRESHOLD")
        self.faq_top_k = int(os.getenv("FAQ_TOP_K", "3"))
        self.seed_path = os.getenv(
            "FAQ_SEED_PATH",
            os.path.join(os.path.dirname(__file__), "..", "data", "seed_faqs.json"),
        )

        # --- Query log ------------------------------------------------
        # PoC uses SQLite for zero-setup. Production swaps to the Postgres
        # whatsapp_queries table (see models/schema.py).
        self.query_log_db = os.getenv(
            "QUERY_LOG_DB",
            os.path.join(os.path.dirname(__file__), "..", "data", "whatsapp_queries.db"),
        )

        # --- Twilio ---------------------------------------------------
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")
        # Off by default so local/ngrok testing is frictionless.
        self.validate_twilio_signature = _get_bool("VALIDATE_TWILIO_SIGNATURE", False)

        # --- Groq LLM (free API) -------------------------------------
        # Key from https://console.groq.com (free). If unset, the assistant
        # falls back to extractive answers from the retrieved context.
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # --- Knowledge base / RAG ------------------------------------
        # ChromaDB persistent store + the synthetic corpus directory.
        self.chroma_dir = os.getenv(
            "CHROMA_DIR",
            os.path.join(os.path.dirname(__file__), "..", "data", "chroma"),
        )
        self.knowledge_dir = os.getenv(
            "KNOWLEDGE_DIR",
            os.path.join(os.path.dirname(__file__), "..", "data", "knowledge"),
        )
        # Raw scraped pages are persisted here as .md files (one-time scrape),
        # then ingested into Chroma alongside the synthetic corpus.
        self.scraped_dir = os.getenv(
            "SCRAPED_DIR",
            os.path.join(os.path.dirname(__file__), "..", "data", "scraped"),
        )
        self.kb_collection = os.getenv("KB_COLLECTION", "kisan_knowledge")
        self.kb_chunk_chars = int(os.getenv("KB_CHUNK_CHARS", "900"))
        self.kb_chunk_overlap = int(os.getenv("KB_CHUNK_OVERLAP", "150"))
        self.kb_top_k = int(os.getenv("KB_TOP_K", "4"))
        # Max rows ingested per CSV/Parquet (Q&A/text shapes) to bound the index.
        self.kb_max_table_rows = int(os.getenv("KB_MAX_TABLE_ROWS", "8000"))
        # Whether build_knowledge.py should attempt live web scraping.
        self.kb_enable_scraping = _get_bool("KB_ENABLE_SCRAPING", True)

        # --- Web search fallback -------------------------------------
        # When the KB's best match scores below kb_min_score, the assistant
        # (if a Groq key is set) searches the web and answers from those
        # results instead of giving a weak/irrelevant KB answer.
        self.kb_min_score = float(os.getenv("KB_MIN_SCORE", "0.35"))
        self.web_search_enabled = _get_bool("WEB_SEARCH_ENABLED", True)
        self.web_search_max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
        self.web_fetch_pages = int(os.getenv("WEB_FETCH_PAGES", "3"))

    @property
    def resolved_backend(self) -> str:
        if self.embedding_backend == "auto":
            return "openai" if self.openai_api_key else "local"
        return self.embedding_backend

    @property
    def match_threshold(self) -> float:
        if self._threshold_override is not None:
            return float(self._threshold_override)
        # Dense OpenAI embeddings separate matches from noise much more
        # sharply than sparse TF-IDF, so the offline demo backend uses a
        # lower cutoff. Tunable on pilot traffic via FAQ_MATCH_THRESHOLD.
        if self.resolved_backend == "openai":
            return 0.80
        return 0.30


@lru_cache
def get_settings() -> Settings:
    return Settings()
