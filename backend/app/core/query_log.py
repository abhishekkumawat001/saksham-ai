"""Lightweight query log for the PoC.

Every inbound WhatsApp message is recorded with the matched FAQ (if any),
the similarity score, and whether it was auto-resolved or escalated. This
table is the raw material for the success metrics in the scoping doc
(auto-resolution rate, escalations, near-misses to tune the threshold).

PoC storage = SQLite (zero setup). Production = the `whatsapp_queries`
Postgres table in models/schema.py. Phone numbers are stored as a SHA-256
hash, never in clear text (PRD: "no PII beyond phone number").
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from app.core.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS whatsapp_queries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at    TEXT NOT NULL,
    phone_hash    TEXT NOT NULL,
    language      TEXT,
    inbound_text  TEXT NOT NULL,
    matched_faq   TEXT,
    score         REAL,
    resolved      INTEGER NOT NULL
);
"""


def _hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()[:32]


def _connect() -> sqlite3.Connection:
    path = get_settings().query_log_db
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(_SCHEMA)
    return conn


def log_query(
    phone: str,
    inbound_text: str,
    language: str,
    matched_faq: Optional[str],
    score: float,
    resolved: bool,
) -> None:
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO whatsapp_queries
               (created_at, phone_hash, language, inbound_text, matched_faq, score, resolved)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                _hash_phone(phone),
                language,
                inbound_text,
                matched_faq,
                round(float(score), 4),
                1 if resolved else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def stats() -> dict:
    """Quick aggregate for the pilot dashboard / sanity checks."""
    conn = _connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM whatsapp_queries").fetchone()[0]
        resolved = conn.execute(
            "SELECT COUNT(*) FROM whatsapp_queries WHERE resolved = 1"
        ).fetchone()[0]
    finally:
        conn.close()
    rate = (resolved / total) if total else 0.0
    return {
        "total_queries": total,
        "auto_resolved": resolved,
        "escalated": total - resolved,
        "auto_resolution_rate": round(rate, 3),
    }
