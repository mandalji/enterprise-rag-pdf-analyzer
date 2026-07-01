"""
rag/chunking.py
===============
WHY THIS FILE EXISTS:
    A whole PDF is too big to feed to an LLM at once, and searching works
    better on smaller pieces. "Chunking" splits long text into overlapping
    pieces. Overlap keeps sentences that straddle a boundary from being lost.

WHAT IT DOES:
    - Recursive chunking: split on paragraphs/sentences, packing up to a size.
    - Semantic chunking: group sentences and start a new chunk when the topic
      shifts (measured by embedding similarity).

HOW IT CONNECTS:
    - services/pdf_service.py produces page texts; the extraction agent calls
      chunk_text() to break them up before they are embedded and stored.
"""

import re
from utils.logger import log


def _split_sentences(text: str) -> list[str]:
    """Naive sentence splitter (no heavy NLP dependency needed)."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def recursive_chunk(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Pack sentences into chunks up to `chunk_size` characters, then start the
    next chunk `overlap` characters back so context carries over.
    """
    sentences = _split_sentences(text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap tail of the previous one.
            tail = current[-overlap:] if overlap and current else ""
            current = f"{tail} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def semantic_chunk(text: str, model_name: str, chunk_size: int) -> list[str]:
    """
    Group consecutive sentences while they stay on-topic. When the similarity
    between the running chunk and the next sentence drops, start a new chunk.
    Falls back to recursive chunking if embeddings are unavailable.
    """
    try:
        import numpy as np
        from rag.embedding import embed_texts

        sentences = _split_sentences(text)
        if len(sentences) <= 1:
            return sentences

        vectors = np.array(embed_texts(sentences, model_name))
        chunks, current, current_vecs = [], [], []
        threshold = 0.55  # lower similarity than this => topic changed

        for i, sentence in enumerate(sentences):
            if not current:
                current.append(sentence)
                current_vecs.append(vectors[i])
                continue
            centroid = np.mean(current_vecs, axis=0)
            sim = float(np.dot(centroid, vectors[i]))  # vectors are normalized
            joined_len = len(" ".join(current))
            if sim < threshold or joined_len > chunk_size:
                chunks.append(" ".join(current))
                current, current_vecs = [sentence], [vectors[i]]
            else:
                current.append(sentence)
                current_vecs.append(vectors[i])
        if current:
            chunks.append(" ".join(current))
        return chunks
    except Exception as exc:  # be resilient for beginners
        log(f"Semantic chunking failed ({exc}); using recursive.", "WARN")
        return recursive_chunk(text, chunk_size, overlap=chunk_size // 6)


def chunk_text(
    text: str,
    strategy: str,
    chunk_size: int,
    overlap: int,
    embedding_model: str,
) -> list[str]:
    """Public entry point: pick a strategy and return chunks."""
    if not text or not text.strip():
        return []
    if strategy == "Semantic":
        return semantic_chunk(text, embedding_model, chunk_size)
    return recursive_chunk(text, chunk_size, overlap)
