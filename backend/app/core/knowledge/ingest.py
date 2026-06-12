"""Build the knowledge base.

Two stages, deliberately separate:
  1. scrape  -> fetch web sources once and SAVE them to data/scraped/*.md
  2. ingest  -> read synthetic corpus + saved scraped files, chunk, embed, store

So you scrape once (slow, network) and can re-ingest/rebuild the Chroma index
freely afterwards (fast, offline) from the saved files.
"""
from __future__ import annotations

import glob
import os
import re
from typing import List

from app.core.config import get_settings
from app.core.knowledge.chunking import Chunk, chunk_markdown
from app.core.knowledge.vector_store import get_store

_SOURCE_RE = re.compile(r"<!--\s*source:\s*(\S+)\s*-->")


def _chunks_from_file(path: str, source_override: str | None = None) -> List[Chunk]:
    settings = get_settings()
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    name = os.path.basename(path)
    # Scraped files embed their origin URL in an HTML comment; use it as source.
    m = _SOURCE_RE.search(text)
    source = source_override or (m.group(1) if m else name)
    title = name.replace("_", " ").replace(".md", "").title()
    return chunk_markdown(
        text,
        source=source,
        default_title=title,
        chunk_chars=settings.kb_chunk_chars,
        overlap=settings.kb_chunk_overlap,
    )


def _load_dir_chunks(directory: str) -> List[Chunk]:
    """Load every supported file in a directory: .md, .csv, .parquet."""
    chunks: List[Chunk] = []
    for path in sorted(glob.glob(os.path.join(directory, "*"))):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".md":
            chunks.extend(_chunks_from_file(path))
        elif ext in (".csv", ".parquet"):
            from app.core.knowledge.tabular import load_table_chunks

            chunks.extend(load_table_chunks(path))
    return chunks


def _load_synthetic_chunks() -> List[Chunk]:
    return _load_dir_chunks(get_settings().knowledge_dir)


def _load_scraped_chunks() -> List[Chunk]:
    return _load_dir_chunks(get_settings().scraped_dir)


def run_scrape() -> int:
    """One-time: fetch all web sources and persist them to data/scraped/."""
    settings = get_settings()
    try:
        from app.core.knowledge.scraper import scrape_and_save
    except Exception as exc:
        print(f"Scraper unavailable ({exc}); skipping web scrape.")
        return 0
    return scrape_and_save(settings.scraped_dir)


def build_knowledge_base(rebuild: bool = False, scrape: bool = True) -> dict:
    """Ingest synthetic + scraped corpora into Chroma.

    scrape=True first fetches the web sources and saves them to disk, then
    ingests everything. scrape=False ingests only what is already on disk
    (synthetic corpus + any previously saved scraped files).
    """
    settings = get_settings()
    store = get_store()
    if rebuild:
        print("Rebuilding: clearing existing collection...")
        store.reset()

    saved = 0
    if scrape:
        saved = run_scrape()
        print(f"Scrape step saved {saved} page(s).")

    synthetic = _load_synthetic_chunks()
    scraped = _load_scraped_chunks()
    print(f"Synthetic corpus: {len(synthetic)} chunks | "
          f"Scraped corpus: {len(scraped)} chunks.")

    all_chunks = synthetic + scraped
    if not all_chunks:
        print("No chunks to ingest.")
        return {"added": 0, "total": store.count()}

    added = store.add(
        texts=[c.text for c in all_chunks],
        sources=[c.source for c in all_chunks],
        titles=[c.title for c in all_chunks],
    )
    total = store.count()
    print(f"Ingested {added} chunks. Collection now holds {total}.")
    return {
        "added": added,
        "total": total,
        "synthetic_chunks": len(synthetic),
        "scraped_chunks": len(scraped),
        "scraped_pages_saved": saved,
    }


def ensure_seeded() -> int:
    """Auto-ingest existing on-disk corpora if the collection is empty.

    Called on API startup so the assistant works immediately. Uses whatever is
    already saved on disk (synthetic + previously scraped) — it never scrapes,
    since that is the explicit build_knowledge.py step.
    """
    store = get_store()
    if store.count() == 0:
        print("Knowledge base empty -> ingesting saved corpora...")
        build_knowledge_base(rebuild=False, scrape=False)
    return store.count()
