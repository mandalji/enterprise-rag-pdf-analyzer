"""
agents/recommendation_agent.py
==============================
WHY THIS FILE EXISTS:
    New users often don't know what to ask. This agent reads the documents and
    proposes smart questions and next actions, lowering the blank-page barrier.

WHAT IT DOES:
    - Pulls broad context.
    - Asks the LLM for JSON with "questions" and "actions".
    - Safely parses the JSON (LLMs sometimes add stray text) and falls back to
      sensible defaults if parsing fails.

HOW IT CONNECTS:
    - Invoked by the Router Agent / the Recommended Questions tab.
    - Uses retrieval_agent, prompts, helpers (extract_json), groq_service.
"""

from agents.retrieval_agent import get_broad_context
from utils.prompts import recommendation_prompt
from utils.helpers import build_context, extract_json
from services.groq_service import chat

_FALLBACK = {
    "questions": [
        "What are the key risks described?",
        "Summarise the main financial findings.",
        "What compliance issues are mentioned?",
        "What are the most important conclusions?",
        "What actions are recommended?",
    ],
    "actions": [
        "Generate an executive summary.",
        "Run a risk analysis.",
        "Compare against related documents.",
    ],
}


def run(store, config, filenames=None) -> dict:
    """Return {"questions": [...], "actions": [...]}. Always returns something."""
    chunks = get_broad_context(store, filenames=filenames, limit=30)
    if not chunks:
        return _FALLBACK

    context = build_context(chunks, max_chars=10000)
    system, user = recommendation_prompt(context)
    raw = chat(
        system, user,
        model=config["model"],
        temperature=0.4,           # a touch more creative for variety
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
    )
    parsed = extract_json(raw)
    if not parsed or "questions" not in parsed:
        return _FALLBACK
    parsed.setdefault("actions", _FALLBACK["actions"])
    return parsed
