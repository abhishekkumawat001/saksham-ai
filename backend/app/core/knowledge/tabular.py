"""Load CSV / Parquet files into knowledge chunks.

Handles the common shapes that show up in agriculture datasets:
  * Q&A pairs        (columns include 'question' + 'answer')  -> one chunk/row
  * instruction text (a single 'text' col, often <s>[INST]..[/INST]..</s>) -> parsed
  * numeric tables   (e.g. crop-yield/fertilizer data)        -> aggregated per
                       category (one summary chunk per crop) instead of 25k rows
  * other small tables -> one "col: val; ..." chunk per row (capped)
"""
from __future__ import annotations

import os
import re
from typing import List

from app.core.config import get_settings
from app.core.knowledge.chunking import Chunk

_INST_RE = re.compile(r"\[INST\](.*?)\[/INST\](.*)", re.DOTALL)
# Column-name preferences for choosing how to group a numeric table.
_GROUP_PREF = ["crop", "label", "commodity", "name", "category", "type", "fertilizer"]


def _read_dataframe(path: str):
    import pandas as pd

    if path.lower().endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _clean_instruction(text: str) -> str:
    text = text.replace("<s>", "").replace("</s>", "").strip()
    m = _INST_RE.search(text)
    if m:
        q, a = m.group(1).strip(), m.group(2).strip()
        return f"Q: {q}\nA: {a}"
    return text.strip()


def _qa_chunks(df, cols, source) -> List[Chunk]:
    qcol, acol = cols["question"], cols["answer"]
    out: List[Chunk] = []
    for _, row in df.iterrows():
        q, a = str(row[qcol]).strip(), str(row[acol]).strip()
        if not q or not a or q.lower() == "nan" or a.lower() == "nan":
            continue
        out.append(Chunk(text=f"Q: {q}\nA: {a}", source=source, title=q[:60]))
    return out


def _text_chunks(df, text_col, source) -> List[Chunk]:
    out: List[Chunk] = []
    for _, row in df.iterrows():
        t = _clean_instruction(str(row[text_col]))
        if not t or t.lower() == "nan":
            continue
        title = t.replace("Q:", "").strip().split("\n")[0][:60]
        out.append(Chunk(text=t, source=source, title=title))
    return out


def _aggregate_table(df, source) -> List[Chunk]:
    import pandas as pd

    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [
        c for c in df.columns
        if not pd.api.types.is_numeric_dtype(df[c]) or df[c].nunique() <= 30
    ]
    # Pick a grouping column: prefer a known crop/label name, else lowest cardinality.
    group_col = None
    for pref in _GROUP_PREF:
        for c in df.columns:
            if c.lower() == pref:
                group_col = c
                break
        if group_col:
            break
    if group_col is None and cat_cols:
        group_col = min(cat_cols, key=lambda c: df[c].nunique())

    out: List[Chunk] = []
    if group_col is not None and df[group_col].nunique() <= 100:
        for val, g in df.groupby(group_col):
            parts = []
            for nc in num_cols:
                parts.append(
                    f"{nc}: avg {g[nc].mean():.1f} (range {g[nc].min():.1f}-{g[nc].max():.1f})"
                )
            for cc in cat_cols:
                if cc == group_col:
                    continue
                top = [str(x) for x in g[cc].value_counts().head(3).index.tolist()]
                if top:
                    parts.append(f"{cc}: commonly {', '.join(top)}")
            text = (
                f"Agronomic profile for {group_col} = {val} "
                f"(from dataset {os.path.basename(source)}, {len(g)} records):\n"
                + "; ".join(parts)
            )
            out.append(Chunk(text=text, source=source, title=f"{group_col}: {val}"))
        return out

    # Fallback: small/unstructured table -> one chunk per row, capped.
    cap = get_settings().kb_max_table_rows
    for _, row in df.head(cap).iterrows():
        text = "; ".join(f"{c}: {row[c]}" for c in df.columns)
        out.append(Chunk(text=text, source=source, title=os.path.basename(source)))
    return out


def load_table_chunks(path: str) -> List[Chunk]:
    """Read a CSV/Parquet file and return knowledge chunks (shape-aware)."""
    settings = get_settings()
    try:
        df = _read_dataframe(path)
    except Exception as exc:
        print(f"  [skip table] {os.path.basename(path)} -> {exc}")
        return []

    df = df.dropna(how="all")
    source = os.path.basename(path)
    cols = {c.lower(): c for c in df.columns}

    if {"question", "answer"} <= set(cols):
        chunks = _qa_chunks(df.head(settings.kb_max_table_rows), cols, source)
        kind = "Q&A"
    elif "text" in cols or df.shape[1] == 1:
        text_col = cols.get("text", df.columns[0])
        chunks = _text_chunks(df.head(settings.kb_max_table_rows), text_col, source)
        kind = "text"
    else:
        chunks = _aggregate_table(df, source)
        kind = "aggregated table"
    print(f"  [table] {source}: {df.shape[0]} rows -> {len(chunks)} chunks ({kind})")
    return chunks
