"""
agents/summary_agent.py
=======================
WHY THIS FILE EXISTS:
    Users want quick summaries at different depths (executive, detailed,
    section, takeaways). This agent produces them from the stored document
    content.

WHAT IT DOES:
    - Pulls a broad sample of chunks (coverage matters more than pinpointing).
    - Builds a summary prompt for the requested mode.
    - Calls the Groq LLM and returns the summary text.

HOW IT CONNECTS:
    - Invoked by the Router Agent / the Executive Summary tab.
    - Uses retrieval_agent (broad context), prompts, helpers, groq_service.
"""

from agents.retrieval_agent import get_broad_context
from utils.prompts import summary_prompt
from utils.helpers import build_context
from services.groq_service import chat


def run(store, mode, config, filenames=None) -> str:
    """mode is one of: Executive, Detailed, Section, Takeaways."""
    chunks = get_broad_context(store, filenames=filenames, limit=40)
    if not chunks:
        return "No document content is available to summarise yet."

    context = build_context(chunks, max_chars=14000)
    system, user = summary_prompt(context, mode)
    return chat(
        system, user,
        model=config["model"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
    )
