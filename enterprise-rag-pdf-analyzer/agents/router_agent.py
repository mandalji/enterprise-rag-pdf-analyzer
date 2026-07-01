"""
agents/router_agent.py
======================
WHY THIS FILE EXISTS:
    This is the "orchestrator" / traffic controller. The UI never calls the
    individual agents directly; it asks the Router to perform a task, and the
    Router decides which specialist agent(s) to run and in what order. This
    keeps the app modular: the UI stays simple and agents stay independent.

WHAT IT DOES:
    - Exposes one function per high-level task (ingest, ask, summarise,
      insight, recommend, compare).
    - Chooses the right agent and passes along the current configuration.

HOW IT CONNECTS:
    - app.py talks ONLY to this file for AI work.
    - This file imports and coordinates every other agent.

MENTAL MODEL:
    UI -> RouterAgent -> (Extraction | Retrieval | QA | Summary |
                          Insight | Recommendation | Comparison)
"""

from agents import (
    extraction_agent,
    qa_agent,
    summary_agent,
    insight_agent,
    recommendation_agent,
    retrieval_agent,
)
from utils.prompts import comparison_prompt
from utils.helpers import build_context
from services.groq_service import chat
from utils.logger import log


class RouterAgent:
    """Coordinates all specialist agents around one shared vector store."""

    def __init__(self, store):
        self.store = store

    # -- INGESTION ----------------------------------------------------------
    def ingest(self, file_bytes, filename, settings_dict):
        log(f"Router -> Extraction Agent for {filename}")
        return extraction_agent.run(file_bytes, filename, self.store, settings_dict)

    # -- QUESTION ANSWERING -------------------------------------------------
    def ask(self, question, config, history_text=""):
        log("Router -> QA Agent")
        return qa_agent.run(self.store, question, config, history_text)

    # -- SUMMARY ------------------------------------------------------------
    def summarise(self, mode, config, filenames=None):
        log(f"Router -> Summary Agent ({mode})")
        return summary_agent.run(self.store, mode, config, filenames)

    # -- INSIGHTS -----------------------------------------------------------
    def insight(self, focus, config, filenames=None):
        log(f"Router -> Insight Agent ({focus})")
        return insight_agent.run(self.store, focus, config, filenames)

    # -- RECOMMENDATIONS ----------------------------------------------------
    def recommend(self, config, filenames=None):
        log("Router -> Recommendation Agent")
        return recommendation_agent.run(self.store, config, filenames)

    # -- MULTI-DOCUMENT COMPARISON -----------------------------------------
    def compare(self, config, filenames):
        log(f"Router -> Comparison over {filenames}")
        # Gather a balanced sample from each file so no document dominates.
        pooled = []
        per_file = max(8, 30 // max(len(filenames), 1))
        for fn in filenames:
            pooled.extend(
                retrieval_agent.get_broad_context(self.store, [fn], limit=per_file)
            )
        if not pooled:
            return "Not enough content across the selected documents to compare."
        context = build_context(pooled, max_chars=14000)
        system, user = comparison_prompt(context)
        return chat(
            system, user,
            model=config["model"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            max_tokens=config["max_tokens"],
        )
