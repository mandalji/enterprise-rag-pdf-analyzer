"""
services/groq_service.py
========================
WHY THIS FILE EXISTS:
    Every agent that needs to "think" sends text to a Groq-hosted open-source
    LLM. This file is the ONLY place that talks to Groq, so if the API ever
    changes you fix it in one spot.

WHAT IT DOES:
    - Creates a Groq client using the API key from config/settings.
    - Provides chat() to send a system+user prompt and get text back.
    - Tracks how many API calls were made (for the Monitoring tab).
    - Handles errors gracefully with clear, beginner-friendly messages.

HOW IT CONNECTS:
    - Imported by every agent in agents/.
    - Reads GROQ_API_KEY and GROQ_MODELS from config/settings.
"""

from functools import lru_cache
from utils.logger import log
from config import settings


class GroqError(Exception):
    """Raised when the Groq API cannot be reached or returns an error."""


@lru_cache(maxsize=1)
def _client():
    """Create and cache the Groq client (one per session)."""
    if not settings.GROQ_API_KEY:
        raise GroqError(
            "No Groq API key found. Add GROQ_API_KEY to Streamlit secrets "
            "(cloud) or your .env file (local)."
        )
    from groq import Groq
    return Groq(api_key=settings.GROQ_API_KEY)


def _bump_call_count():
    """Increment the API call counter kept in session_state."""
    try:
        import streamlit as st
        st.session_state.api_calls = st.session_state.get("api_calls", 0) + 1
    except Exception:
        pass


def chat(
    system: str,
    user: str,
    model: str,
    temperature: float = settings.DEFAULT_TEMPERATURE,
    top_p: float = settings.DEFAULT_TOP_P,
    max_tokens: int = settings.DEFAULT_MAX_TOKENS,
) -> str:
    """
    Send one system + user message to Groq and return the model's text reply.
    Raises GroqError with a readable message on failure.
    """
    try:
        client = _client()
        _bump_call_count()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content or ""
    except GroqError:
        raise
    except Exception as exc:
        log(f"Groq API error: {exc}", "ERROR")
        raise GroqError(f"Groq request failed: {exc}") from exc
