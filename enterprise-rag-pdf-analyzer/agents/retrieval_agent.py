"""
agents/retrieval_agent.py
=========================
WHY THIS FILE EXISTS:
    Several agents (QA, Summary, Insight, Recommendation, Comparison) need the
    same thing: "get me the most relevant chunks for X". This agent centralises
    that logic so retrieval behaviour is consistent everywhere.

WHAT IT DOES:
    - Wraps rag/retrieval.retrieve() with the user's chosen search type & top_k.
    - Can also fetch a broad sample of chunks (for summaries/comparisons that
      need coverage rather than a pinpoint answer).

HOW IT CONNECTS:
    - Called by the Router Agent and by the other reasoning agents.
    - Reads from the shared VectorStore instance.
"""

from rag.retrieval import retrieve


def get_context(store, query, search_type, top_k, filenames=None):
    """Return the top relevant chunks for a specific query."""
    return retrieve(store, query, search_type, top_k, filenames)


def get_broad_context(store, filenames=None, limit=40):
    """
    Return a wide sample of chunks across the document(s). Used when the task
    is 'summarise everything' rather than 'answer this narrow question'.
    """
    return store.get_all(filenames=filenames, limit=limit)
