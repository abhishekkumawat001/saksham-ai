"""Build/refresh the KisanSaathi knowledge base.

Loads the synthetic agronomy corpus AND scrapes the curated agriculture web
sources, chunks everything, embeds with the HuggingFace MiniLM model and stores
it in ChromaDB.

Usage (from the backend/ folder):
    python build_knowledge.py                 # synthetic + scraping, rebuild
    python build_knowledge.py --no-scrape     # synthetic corpus only (fast)
    python build_knowledge.py --keep          # add to existing, don't wipe
"""
from __future__ import annotations

import argparse

from app.core.knowledge.ingest import build_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the knowledge base.")
    parser.add_argument("--no-scrape", action="store_true",
                        help="skip web scraping, use the synthetic corpus only")
    parser.add_argument("--keep", action="store_true",
                        help="keep existing chunks instead of rebuilding")
    args = parser.parse_args()

    stats = build_knowledge_base(rebuild=not args.keep, scrape=not args.no_scrape)
    print("\nDone:", stats)


if __name__ == "__main__":
    main()
