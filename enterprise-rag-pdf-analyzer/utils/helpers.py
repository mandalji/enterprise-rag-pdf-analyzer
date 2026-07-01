"""
utils/helpers.py
================
WHY THIS FILE EXISTS:
    Small, generic helper functions that several files need. Keeping them here
    avoids copy-pasting the same little utilities everywhere.

WHAT IT DOES:
    - Formats retrieved chunks into a single context string with source labels.
    - Extracts clean JSON out of an LLM response (models sometimes wrap JSON
      in markdown fences or add stray text).
    - Formats file sizes for display.

HOW IT CONNECTS:
    - Used by agents/ (context building, JSON parsing) and app.py (display).
"""

import json
import re


def build_context(chunks: list[dict], max_chars: int = 12000) -> str:
    """
    Turn a list of retrieved chunk dicts into one context string.
    Each chunk dict looks like:
        {"text": "...", "metadata": {"filename": "...", "page": 1, "chunk_id": "..."}}
    We prefix each chunk with its source so the LLM can cite it.
    """
    parts = []
    total = 0
    for c in chunks:
        meta = c.get("metadata", {})
        label = f"[{meta.get('filename', 'unknown')} p.{meta.get('page', '?')}]"
        piece = f"{label}\n{c.get('text', '')}\n"
        if total + len(piece) > max_chars:
            break
        parts.append(piece)
        total += len(piece)
    return "\n".join(parts)


def extract_json(text: str):
    """
    Best-effort extraction of a JSON object from an LLM reply.
    Handles ```json fences and leading/trailing prose.
    Returns a Python object, or None if parsing fails.
    """
    if not text:
        return None
    # Remove markdown code fences.
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    # Try direct parse first.
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Fall back: grab the first {...} block.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def human_size(num_bytes: int) -> str:
    """Convert a byte count into a friendly string like '1.2 MB'."""
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
