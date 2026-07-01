"""
rag/retrieval.py
================
WHY THIS FILE EXISTS:
    Plain similarity search sometimes returns several chunks that all say the
    same thing. This file adds smarter retrieval strategies so the context we
    hand to the LLM is both relevant AND diverse.

WHAT IT DOES:
    - Similarity: return the closest chunks (delegates to the vector store).
    - MMR (Maximal Marginal Relevance): pick chunks that are relevant but also
      different from each other, reducing redundancy.
    - Hybrid: combine vector similarity with simple keyword overlap so exact
      terms (names, codes) are not missed.

HOW IT CONNECTS:
    - The Retrieval Agent calls retrieve() with the search type chosen in the UI.
    - Uses rag/vector_store.VectorStore and rag/embedding.
"""

import numpy as np
from rag.embedding import embed_query, embed_texts


def _similarity(store, question, top_k, filenames):
    return store.query(question, top_k, filenames)


def _mmr(store, question, top_k, filenames, lambda_mult=0.6, pool=20):
    """
    Fetch a larger candidate pool, then greedily select chunks that maximise
    relevance to the query while minimising similarity to already-picked ones.
    """
    candidates = store.query(question, min(pool, max(top_k * 4, 8)), filenames)
    if len(candidates) <= top_k:
        return candidates

    texts = [c["text"] for c in candidates]
    cand_vecs = np.array(embed_texts(texts, store.embedding_model))
    qvec = np.array(embed_query(question, store.embedding_model))

    query_sim = cand_vecs @ qvec  # relevance to the question
    selected, selected_idx = [], []
    remaining = list(range(len(candidates)))

    for _ in range(top_k):
        best_score, best_i = -1e9, None
        for i in remaining:
            if selected_idx:
                redundancy = max(cand_vecs[i] @ cand_vecs[j] for j in selected_idx)
            else:
                redundancy = 0.0
            score = lambda_mult * query_sim[i] - (1 - lambda_mult) * redundancy
            if score > best_score:
                best_score, best_i = score, i
        selected.append(candidates[best_i])
        selected_idx.append(best_i)
        remaining.remove(best_i)
    return selected


def _hybrid(store, question, top_k, filenames):
    """
    Blend vector similarity with keyword overlap. We over-fetch by vector
    search, then boost chunks that literally contain query words.
    """
    candidates = store.query(question, max(top_k * 3, 9), filenames)
    q_words = {w.lower() for w in question.split() if len(w) > 2}

    def keyword_score(text):
        words = {w.lower() for w in text.split()}
        return len(q_words & words)

    for c in candidates:
        # distance: lower is better -> convert to a similarity-like value.
        vec_sim = 1.0 - (c["distance"] if c["distance"] is not None else 0.5)
        c["_hybrid"] = vec_sim + 0.1 * keyword_score(c["text"])
    candidates.sort(key=lambda c: c["_hybrid"], reverse=True)
    return candidates[:top_k]


def retrieve(store, question, search_type, top_k, filenames=None):
    """Public entry point used by the Retrieval Agent."""
    if search_type == "MMR":
        return _mmr(store, question, top_k, filenames)
    if search_type == "Hybrid":
        return _hybrid(store, question, top_k, filenames)
    return _similarity(store, question, top_k, filenames)
