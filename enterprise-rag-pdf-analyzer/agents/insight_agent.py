"""
agents/insight_agent.py
=======================
WHY THIS FILE EXISTS:
    Beyond plain summaries, enterprises want analysis: risks, opportunities,
    compliance concerns, and trends. This agent produces those structured,
    evidence-based insights.

WHAT IT DOES:
    - Pulls broad document context.
    - Builds a focus-specific prompt (Risks / Opportunities / Compliance / Trends).
    - Calls the Groq LLM and returns the analysis text.

HOW IT CONNECTS:
    - Invoked by the Router Agent / the Enterprise Insights tab.
    - Uses retrieval_agent, prompts, helpers, groq_service.
"""

from agents.retrieval_agent import get_broad_context
from utils.prompts import insight_prompt
from utils.helpers import build_context
from services.groq_service import chat


def run(store, focus, config, filenames=None) -> str:
    """focus is one of: Risks, Opportunities, Compliance, Trends."""
    chunks = get_broad_context(store, filenames=filenames, limit=40)
    if not chunks:
        return "No document content is available to analyse yet."

    context = build_context(chunks, max_chars=14000)
    system, user = insight_prompt(context, focus)
    return chat(
        system, user,
        model=config["model"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
    )
