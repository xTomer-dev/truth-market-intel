"""
Section-aware paragraph segmenter for SEC filings.

Contract
--------
split_paragraphs(text) → list[dict] with keys:
    speaker    - section label (e.g. "Item 1A"); stored in SpeakerBlock.speaker (nullable column)
    text       - segment text
    char_start - byte offset into the normalized source text (int)
    char_end   - byte offset into the normalized source text (int)

char_start / char_end are computed here and available to downstream code.
They are NOT persisted — SpeakerBlock has no such columns.
If a downstream use case needs persisted offsets, add an Alembic migration
to add char_start / char_end Integer columns to speaker_blocks.

Section detection
-----------------
Lightweight regex-only detection of SEC-style section headers:
    Item 1.  Item 1A.  Item 8.01  ITEM 7A  Part I  PART II  etc.
When a header line is found it updates current_section; the header
itself is not emitted as a segment.
If no section is detected, the segment gets section = "unknown".
"""

import re
from dataclasses import dataclass
from typing import Optional


MIN_SEGMENT_CHARS = 80
MAX_SEGMENT_CHARS = 2000

# Detects "Item 1", "Item 1A", "Item 8.01", "Part I", "Part II", etc.
# Case-insensitive; matches at start of a (possibly indented) line.
_HEADER_LINE_RE = re.compile(
    r"^\s*(item\s+\d+(?:\.\d+)?[a-z]?|part\s+[ivx]+)\b",
    re.IGNORECASE,
)

# Extracts and normalizes just the label portion ("item 1a" → "Item 1A")
_LABEL_RE = re.compile(
    r"(item\s+\d+(?:\.\d+)?[a-z]?|part\s+[ivx]+)",
    re.IGNORECASE,
)


@dataclass
class DigestedSegment:
    """Explicit internal contract for a labeled segment.

    Returned by split_paragraphs (via dict adapter). When persisted to DB:
        position  → SpeakerBlock.block_index
        section   → SpeakerBlock.speaker  (nullable; "unknown" when undetected)
        text      → SpeakerBlock.text
        char_start, char_end → NOT persisted (no DB column)
    """
    document_id: Optional[int]  # None before DB write
    position: int
    section: str
    text: str
    char_start: int
    char_end: int


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_label(raw: str) -> str:
    """'item 1a' → 'Item 1A', 'PART II' → 'Part II', 'item 8.01' → 'Item 8.01'."""
    parts = raw.split()
    result = []
    for p in parts:
        if re.fullmatch(r"[ivxIVX]+", p):
            # roman numeral → all-uppercase
            result.append(p.upper())
        elif re.fullmatch(r"\d+(?:\.\d+)?[a-zA-Z]?", p):
            # digit token like "1", "1A", "8.01" → uppercase any trailing letter
            result.append(p.upper())
        else:
            result.append(p.capitalize())
    return " ".join(result)


def _extract_section_label(line: str) -> Optional[str]:
    m = _LABEL_RE.search(line)
    if not m:
        return None
    return _normalize_label(m.group(1))


def _split_with_offsets(text: str) -> list[tuple[int, int, str]]:
    """Split text on blank lines; return (char_start, char_end, content)."""
    result = []
    sep = re.compile(r"\n\s*\n")
    pos = 0
    for m in sep.finditer(text):
        chunk = text[pos : m.start()]
        content = chunk.strip()
        if content:
            leading = len(chunk) - len(chunk.lstrip())
            cs = pos + leading
            result.append((cs, cs + len(content), content))
        pos = m.end()
    # trailing chunk
    chunk = text[pos:]
    content = chunk.strip()
    if content:
        leading = len(chunk) - len(chunk.lstrip())
        cs = pos + leading
        result.append((cs, cs + len(content), content))
    return result


def _split_long(text: str) -> list[str]:
    """Split a single chunk that exceeds MAX_SEGMENT_CHARS on sentence breaks."""
    if len(text) <= MAX_SEGMENT_CHARS:
        return [text]

    # Split on ". " followed by a capital letter (sentence boundary heuristic)
    sentences = re.split(r"(?<=\. )(?=[A-Z])", text)
    chunks: list[str] = []
    buf: list[str] = []
    for sent in sentences:
        candidate = (" ".join(buf + [sent])) if buf else sent
        if len(candidate) > MAX_SEGMENT_CHARS and buf:
            chunks.append(" ".join(buf))
            buf = [sent]
        else:
            buf.append(sent)
    if buf:
        chunks.append(" ".join(buf))
    return [c for c in chunks if len(c) >= MIN_SEGMENT_CHARS]


# ── Public API ────────────────────────────────────────────────────────────────

def split_paragraphs(text: str) -> list[dict]:
    """Section-aware paragraph segmentation.

    Returns list of dicts compatible with SpeakerBlock write in pipeline.py:
        {"speaker": section, "text": ..., "char_start": int, "char_end": int}

    pipeline.py consumes only "speaker" and "text"; char_start/char_end are
    carried for downstream use but not written to DB.
    """
    raw = _split_with_offsets(text)
    current_section = "unknown"
    result: list[dict] = []

    for char_start, char_end, chunk in raw:
        # Detect section header: short chunk whose first line matches Item/Part
        first_line = chunk.split("\n")[0]
        if _HEADER_LINE_RE.match(first_line) and len(chunk) < 200:
            label = _extract_section_label(first_line)
            if label:
                current_section = label
            continue  # header is not a content segment

        if len(chunk) < MIN_SEGMENT_CHARS:
            continue

        # Long chunk: split on sentence boundaries, distribute char range
        if len(chunk) > MAX_SEGMENT_CHARS:
            sub_texts = _split_long(chunk)
            span = char_end - char_start
            total = sum(len(s) for s in sub_texts) or 1
            cursor = char_start
            for sub in sub_texts:
                sub_end = cursor + int(len(sub) / total * span)
                result.append(
                    {
                        "speaker": current_section,
                        "text": sub,
                        "char_start": cursor,
                        "char_end": sub_end,
                    }
                )
                cursor = sub_end
        else:
            result.append(
                {
                    "speaker": current_section,
                    "text": chunk,
                    "char_start": char_start,
                    "char_end": char_end,
                }
            )

    return result
