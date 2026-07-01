"""
rag/embedding.py
================
WHY THIS FILE EXISTS:
    Computers cannot compare text directly. "Embeddings" convert text into
    lists of numbers (vectors) where similar meanings produce similar numbers.
    This file loads a free, open-source embedding model and turns text into
    those vectors.

WHAT IT DOES:
    - Loads a sentence-transformers model (cached so it loads only once).
    - Provides embed_texts() to convert a list of strings into vectors.

HOW IT CONNECTS:
    - rag/vector_store.py uses it to embed chunks before storing them and to
      embed the user's query before searching.
    - The model choice comes from config/settings.EMBEDDING_MODELS.

NOTE FOR BEGINNERS:
    The first time a model is used it is downloaded (a few hundred MB). On
    Streamlit Cloud this happens automatically on first run.
"""

from functools import lru_cache
from utils.logger import log


@lru_cache(maxsize=2)
def _get_model(model_name: str):
    """Load and cache a sentence-transformers model by name."""
    from sentence_transformers import SentenceTransformer
    log(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    """
    Convert a list of strings into a list of embedding vectors.
    Returns a plain Python list so it is easy to store in ChromaDB.
    """
    model = _get_model(model_name)
    vectors = model.encode(
        texts,
        normalize_embeddings=True,   # helps cosine similarity behave well
        show_progress_bar=False,
    )
    return vectors.tolist()


def embed_query(text: str, model_name: str) -> list[float]:
    """Embed a single query string and return one vector."""
    return embed_texts([text], model_name)[0]
