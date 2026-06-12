"""Split documents into overlapping, heading-aware chunks for embedding."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")


@dataclass
class Chunk:
    text: str
    source: str           # e.g. "fertilizers.md" or a URL
    title: str            # nearest markdown heading / page title
    metadata: dict = field(default_factory=dict)


def _split_paragraphs(text: str) -> List[str]:
    # Split on blank lines; keep non-empty, stripped paragraphs.
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_markdown(
    text: str,
    source: str,
    default_title: str,
    chunk_chars: int = 900,
    overlap: int = 150,
) -> List[Chunk]:
    """Pack paragraphs into ~chunk_chars chunks, tracking the current heading.

    A block may start with a markdown heading immediately followed by its body
    (no blank line). We lift the heading into the chunk title and keep the body
    as content. Overlap carries the tail of one chunk into the next so context
    is not lost at boundaries.
    """
    chunks: List[Chunk] = []
    current_title = default_title
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf.strip():
            chunks.append(Chunk(text=buf.strip(), source=source, title=current_title))
        buf = ""

    def add_para(para: str) -> None:
        nonlocal buf
        if not para:
            return
        if not buf:
            buf = para
        elif len(buf) + len(para) + 2 <= chunk_chars:
            buf += "\n\n" + para
        else:
            prev = buf
            flush()
            tail = prev[-overlap:] if overlap else ""
            buf = (tail + "\n\n" + para).strip() if tail else para

    for block in _split_paragraphs(text):
        if _HEADING_RE.match(block):
            # New section: flush the previous one and update the title.
            flush()
            nl = block.find("\n")
            heading_line = block if nl == -1 else block[:nl]
            current_title = _HEADING_RE.match(heading_line).group(2).strip()
            body = "" if nl == -1 else block[nl + 1:].strip()
            add_para(body)
        else:
            add_para(block)
    flush()
    return chunks
