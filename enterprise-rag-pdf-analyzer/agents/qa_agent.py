"""
agents/qa_agent.py
==================
WHY THIS FILE EXISTS:
    This agent answers the user's questions. It is the core of the "chat with
    your documents" experience and is designed to reduce hallucination by
    forcing the model to rely only on retrieved context and to cite sources.

WHAT IT DOES:
    - Retrieves relevant chunks (via the Retrieval Agent).
    - Builds a grounded prompt (via utils/prompts.qa_prompt).
    - Calls the Groq LLM (via services/groq_service).
    - Returns the answer plus the source list for citation display.

HOW IT CONNECTS:
    - Invoked by the Router Agent for question-style requests.
    - Uses retrieval_agent, prompts, helpers, and groq_service.
"""

from agents.retrieval_agent import get_context
from utils.prompts import qa_prompt
from utils.helpers import build_context
from services.groq_service import chat


def run(store, question, config, history_text="") -> dict:
    """
    config is a dict with: model, temperature, top_p, max_tokens,
    search_type, top_k, filenames (optional).
    Returns: {"answer": str, "sources": [ {filename, page, chunk_id} ]}.
    """
    chunks = get_context(
        store,
        question,
        config["search_type"],
        config["top_k"],
        config.get("filenames"),
    )

    if not chunks:
        return {
            "answer": "I couldn't find anything relevant in the uploaded "
                      "documents. Try uploading a document or rephrasing.",
            "sources": [],
        }

    context = build_context(chunks)
    system, user = qa_prompt(question, context, history_text)
    answer = chat(
        system, user,
        model=config["model"],
        temperature=config["temperature"],
        top_p=config["top_p"],
        max_tokens=config["max_tokens"],
    )

    sources = [
        {
            "filename": c["metadata"].get("filename"),
            "page": c["metadata"].get("page"),
            "chunk_id": c["metadata"].get("chunk_id"),
        }
        for c in chunks
    ]
    return {"answer": answer, "sources": sources}
