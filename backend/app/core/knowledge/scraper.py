"""Web scraper for agriculture knowledge pages (one-time build step).

Fetches each source, reduces it to clean main-body text, and persists it to
disk as a markdown file under data/scraped/. The ingestion step then reads
those saved files (plus the synthetic corpus) into ChromaDB. Separating
"fetch from web" (slow, run once) from "ingest into Chroma" (fast, repeatable)
is deliberate, so you scrape once and rebuild the index freely afterwards.

Extraction uses trafilatura when available, falling back to a BeautifulSoup
<p> grab. Every fetch is isolated so one unreachable/blocked page never breaks
the run — the synthetic corpus is always there as a reliable base.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional

# Curated, stable, public sources covering the requested topics. Wikipedia is
# used because it is reliable to scrape and CC-licensed; extend SOURCES freely.
SOURCES: List[str] = [
    # Fertilizers & plant nutrition
    "https://en.wikipedia.org/wiki/Fertilizer",
    "https://en.wikipedia.org/wiki/Urea",
    "https://en.wikipedia.org/wiki/Diammonium_phosphate",
    "https://en.wikipedia.org/wiki/Potash",
    "https://en.wikipedia.org/wiki/Compost",
    "https://en.wikipedia.org/wiki/Vermicompost",
    "https://en.wikipedia.org/wiki/Micronutrient",
    "https://en.wikipedia.org/wiki/Plant_nutrition",
    "https://en.wikipedia.org/wiki/Soil_pH",
    # Seeds
    "https://en.wikipedia.org/wiki/Seed",
    "https://en.wikipedia.org/wiki/Germination",
    "https://en.wikipedia.org/wiki/Seed_treatment",
    # Cereals / wheat & other staples
    "https://en.wikipedia.org/wiki/Wheat",
    "https://en.wikipedia.org/wiki/Common_wheat",
    "https://en.wikipedia.org/wiki/Durum",
    "https://en.wikipedia.org/wiki/Rice",
    "https://en.wikipedia.org/wiki/Maize",
    # Vegetables
    "https://en.wikipedia.org/wiki/Tomato",
    "https://en.wikipedia.org/wiki/Onion",
    "https://en.wikipedia.org/wiki/Potato",
    "https://en.wikipedia.org/wiki/Chili_pepper",
    "https://en.wikipedia.org/wiki/Eggplant",
    "https://en.wikipedia.org/wiki/Okra",
    # Flowers
    "https://en.wikipedia.org/wiki/Tagetes",
    "https://en.wikipedia.org/wiki/Rose",
    "https://en.wikipedia.org/wiki/Chrysanthemum",
    "https://en.wikipedia.org/wiki/Jasmine",
    # General practice
    "https://en.wikipedia.org/wiki/Crop_rotation",
    "https://en.wikipedia.org/wiki/Integrated_pest_management",
    "https://en.wikipedia.org/wiki/Drip_irrigation",
    "https://en.wikipedia.org/wiki/Powdery_mildew",
]

_HEADERS = {"User-Agent": "KisanSaathi-KB/1.0 (educational agriculture assistant)"}
_TIMEOUT = 20
_MAX_CHARS = 20000  # keep substantial article body, still bounded


@dataclass
class ScrapedDoc:
    url: str
    title: str
    text: str


def _extract_trafilatura(html: str, url: str) -> Optional[str]:
    try:
        import trafilatura

        return trafilatura.extract(
            html, url=url, include_comments=False, include_tables=False,
            favor_recall=True,
        )
    except Exception:
        return None


def _extract_bs4(html: str) -> Optional[str]:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        paras = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = "\n\n".join(p for p in paras if len(p) > 40)
        return text or None
    except Exception:
        return None


def _title_of(html: str, fallback: str) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.replace(" - Wikipedia", "").strip()
    except Exception:
        pass
    return fallback


def slugify(url: str) -> str:
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return name[:80] or "page"


def scrape_url(url: str) -> Optional[ScrapedDoc]:
    """Fetch one URL and return cleaned text, or None on any failure."""
    try:
        import requests

        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:  # network error, timeout, blocked, etc.
        print(f"  [skip] {url} -> {exc}")
        return None

    text = _extract_trafilatura(html, url) or _extract_bs4(html)
    if not text or len(text) < 200:
        print(f"  [skip] {url} -> no usable text extracted")
        return None
    text = text[:_MAX_CHARS]
    title = _title_of(html, url)
    print(f"  [ok]   {url} -> '{title}' ({len(text)} chars)")
    return ScrapedDoc(url=url, title=title, text=text)


def scrape_all(urls: Optional[List[str]] = None, delay: float = 0.5) -> List[ScrapedDoc]:
    targets = urls if urls is not None else SOURCES
    docs: List[ScrapedDoc] = []
    print(f"Scraping {len(targets)} source(s)...")
    for url in targets:
        doc = scrape_url(url)
        if doc:
            docs.append(doc)
        if delay:
            time.sleep(delay)  # be polite to the servers
    print(f"Scraped {len(docs)}/{len(targets)} successfully.")
    return docs


def save_scraped(docs: List[ScrapedDoc], out_dir: str) -> int:
    """Persist scraped docs to out_dir as markdown files. Returns count saved."""
    os.makedirs(out_dir, exist_ok=True)
    for doc in docs:
        path = os.path.join(out_dir, f"{slugify(doc.url)}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"# {doc.title}\n\n")
            fh.write(f"<!-- source: {doc.url} -->\n\n")
            fh.write(doc.text.strip() + "\n")
    print(f"Saved {len(docs)} page(s) to {out_dir}")
    return len(docs)


def scrape_and_save(out_dir: str, urls: Optional[List[str]] = None) -> int:
    """One-time: fetch all sources and persist them to out_dir."""
    docs = scrape_all(urls)
    return save_scraped(docs, out_dir)
