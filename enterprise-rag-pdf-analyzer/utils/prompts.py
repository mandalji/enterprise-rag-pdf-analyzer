"""
utils/prompts.py
================
WHY THIS FILE EXISTS:
    The "brains" of each agent is really a well-written prompt. Keeping all
    prompts in one place means you can improve the AI's behaviour without
    hunting through code. This is the most important file to edit if you want
    to change *how* the assistant answers.

WHAT IT DOES:
    - Stores reusable prompt templates as Python functions.
    - Each function returns a (system_prompt, user_prompt) pair.

HOW IT CONNECTS:
    - Imported by every agent in agents/ to build its LLM request.
"""


# ---------------------------------------------------------------------------
# QA AGENT
# ---------------------------------------------------------------------------
def qa_prompt(question: str, context: str, history: str = "") -> tuple[str, str]:
    system = (
        "You are a meticulous enterprise document analyst. "
        "Answer ONLY using the provided context. "
        "If the answer is not in the context, say clearly that the documents "
        "do not contain that information. Never invent facts. "
        "When you use information, mention the source in the form "
        "[filename p.PAGE]. Be concise and professional."
    )
    user = (
        f"Conversation so far (may be empty):\n{history}\n\n"
        f"Context extracted from the documents:\n---\n{context}\n---\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above and cite sources."
    )
    return system, user


# ---------------------------------------------------------------------------
# SUMMARY AGENT
# ---------------------------------------------------------------------------
def summary_prompt(context: str, mode: str) -> tuple[str, str]:
    system = (
        "You are an expert at summarising business and technical documents. "
        "Base your summary strictly on the supplied text."
    )
    instructions = {
        "Executive": "Write a tight executive summary (5-8 bullet points) for a busy leader.",
        "Detailed": "Write a thorough, well-structured summary covering all major sections.",
        "Section": "Summarise the document section by section with short headers.",
        "Takeaways": "List the 6-10 most important key takeaways as bullet points.",
    }
    instruction = instructions.get(mode, instructions["Executive"])
    user = f"{instruction}\n\nDocument text:\n---\n{context}\n---"
    return system, user


# ---------------------------------------------------------------------------
# INSIGHT AGENT
# ---------------------------------------------------------------------------
def insight_prompt(context: str, focus: str) -> tuple[str, str]:
    system = (
        "You are a senior enterprise risk, compliance, and strategy consultant. "
        "Analyse the document text and produce actionable, evidence-based insights. "
        "Only use what is supported by the text."
    )
    focus_map = {
        "Risks": "Identify the key RISKS. For each: risk, why it matters, severity (Low/Med/High).",
        "Opportunities": "Identify OPPORTUNITIES for value creation or improvement.",
        "Compliance": "Identify COMPLIANCE / regulatory / legal considerations and gaps.",
        "Trends": "Identify notable TRENDS, patterns, or trajectories in the content.",
    }
    instruction = focus_map.get(focus, focus_map["Risks"])
    user = f"{instruction}\n\nDocument text:\n---\n{context}\n---"
    return system, user


# ---------------------------------------------------------------------------
# RECOMMENDATION AGENT
# ---------------------------------------------------------------------------
def recommendation_prompt(context: str) -> tuple[str, str]:
    system = (
        "You generate smart, specific questions a user could ask about a "
        "document set, plus suggested next actions. Output valid JSON only."
    )
    user = (
        "Based on the document text below, return a JSON object with exactly "
        "two keys: \"questions\" (a list of 5 concise, insightful questions) "
        "and \"actions\" (a list of 3 recommended next actions). "
        "Return ONLY the JSON, no markdown, no commentary.\n\n"
        f"Document text:\n---\n{context}\n---"
    )
    return system, user


# ---------------------------------------------------------------------------
# MULTI-DOCUMENT COMPARISON
# ---------------------------------------------------------------------------
def comparison_prompt(context: str) -> tuple[str, str]:
    system = (
        "You compare multiple documents objectively. Base every statement on "
        "the supplied text and cite which document each point comes from."
    )
    user = (
        "The context below contains excerpts from MULTIPLE documents "
        "(each chunk is labelled with its filename). Produce three sections:\n"
        "1. SIMILARITIES\n2. DIFFERENCES\n3. CONTRADICTIONS (if any)\n\n"
        f"Context:\n---\n{context}\n---"
    )
    return system, user
