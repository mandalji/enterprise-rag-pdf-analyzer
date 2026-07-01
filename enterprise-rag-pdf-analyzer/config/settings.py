"""
config/settings.py
==================
WHY THIS FILE EXISTS:
    This is the single "control panel" for the whole application. Instead of
    scattering magic numbers, model names, and API keys across many files,
    everything configurable lives here. Every other file imports from here.

WHAT IT DOES:
    - Loads the Groq API key from environment variables / Streamlit secrets.
    - Defines the list of open-source Groq models the user can pick.
    - Defines the embedding models the user can pick.
    - Holds sensible defaults for chunking, retrieval, and generation.

HOW IT CONNECTS:
    - services/groq_service.py       -> reads GROQ_API_KEY and model list.
    - rag/embedding.py               -> reads EMBEDDING_MODELS.
    - rag/chunking.py, retrieval.py  -> read default chunk/retrieval values.
    - app.py                         -> reads everything to build the sidebar.
"""

import os

# ---------------------------------------------------------------------------
# API KEY LOADING
# ---------------------------------------------------------------------------
# On Streamlit Cloud the key comes from st.secrets. Locally it comes from a
# .env file (loaded by python-dotenv). We try both so the app "just works"
# in either place.
def _load_api_key() -> str:
    # 1) Try Streamlit secrets (used on Streamlit Cloud).
    try:
        import streamlit as st  # imported lazily so non-UI code still works
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    # 2) Try a local .env file.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    # 3) Fall back to a normal environment variable.
    return os.environ.get("GROQ_API_KEY", "")


GROQ_API_KEY = _load_api_key()

# ---------------------------------------------------------------------------
# LLM MODELS (all open-source, served by Groq)
# ---------------------------------------------------------------------------
# Keys are friendly names shown in the UI; values are the exact Groq model IDs.
GROQ_MODELS = {
    "Llama 3.3 70B (recommended)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (fast/cheap)":   "llama-3.1-8b-instant",
    "DeepSeek R1 Distill 70B":     "deepseek-r1-distill-llama-70b",
    "Gemma2 9B":                   "gemma2-9b-it",
}

DEFAULT_MODEL_LABEL = "Llama 3.3 70B (recommended)"

# ---------------------------------------------------------------------------
# EMBEDDING MODELS (free, open-source, run locally via sentence-transformers)
# ---------------------------------------------------------------------------
EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2 (fast, 384d)": "sentence-transformers/all-MiniLM-L6-v2",
    "BGE-small-en-v1.5 (accurate, 384d)": "BAAI/bge-small-en-v1.5",
}

DEFAULT_EMBEDDING_LABEL = "all-MiniLM-L6-v2 (fast, 384d)"

# ---------------------------------------------------------------------------
# GENERATION DEFAULTS
# ---------------------------------------------------------------------------
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# CHUNKING DEFAULTS
# ---------------------------------------------------------------------------
DEFAULT_CHUNK_SIZE = 800          # characters per chunk
DEFAULT_CHUNK_OVERLAP = 120       # characters shared between neighbours
CHUNK_STRATEGIES = ["Recursive", "Semantic"]

# ---------------------------------------------------------------------------
# RETRIEVAL DEFAULTS
# ---------------------------------------------------------------------------
SEARCH_TYPES = ["Similarity", "MMR", "Hybrid"]
DEFAULT_TOP_K = 4                 # number of chunks returned

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma")
os.makedirs(CHROMA_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# APP METADATA (shown in sidebar About section)
# ---------------------------------------------------------------------------
APP_TITLE = "Enterprise Agentic RAG PDF Analyzer"
APP_VERSION = "1.0.0 (MVP)"
DEVELOPER = "Built with Streamlit + Groq + ChromaDB"
