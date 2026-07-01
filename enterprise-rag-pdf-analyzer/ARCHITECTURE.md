# 🏗️ Architecture — how every file fits together

This document explains, in plain language, **why each file exists, what it does,
and how it connects** to the others. Read it top to bottom to understand the
whole system.

---

## 1. The big idea

The app is a **RAG (Retrieval-Augmented Generation)** system with an
**agentic** layer on top:

- **RAG** = instead of asking the LLM to answer from memory (which causes made-up
  answers), we first *retrieve* the most relevant pieces of your documents and
  hand them to the LLM as context. The LLM answers using only that context.
- **Agentic** = rather than one giant function, work is split into small
  "agents", each with one job. A **Router Agent** decides which agent runs.

---

## 2. Request flow

```
You (browser)
   │  upload / ask / click
   ▼
app.py  (Streamlit UI — collects settings, shows results)
   │  calls exactly one object:
   ▼
RouterAgent  (agents/router_agent.py — the traffic controller)
   │  picks the right specialist:
   ├── Extraction Agent  → services/pdf_service → rag/chunking → rag/vector_store
   ├── Retrieval Agent   → rag/retrieval → rag/vector_store → rag/embedding
   ├── QA Agent          → Retrieval + utils/prompts + services/groq_service
   ├── Summary Agent     → Retrieval + prompts + groq_service
   ├── Insight Agent     → Retrieval + prompts + groq_service
   └── Recommendation Ag.→ Retrieval + prompts + groq_service
```

---

## 3. Layer-by-layer

### `config/settings.py` — the control panel
The single source of truth for API keys, model lists, and default values.
Everything else imports from here, so you change behaviour in one place.

### `utils/` — shared tools
- **logger.py** — records events so the UI can show Processing Logs.
- **prompts.py** — every instruction sent to the LLM. Edit this to change tone
  or behaviour. This is the "personality" of each agent.
- **helpers.py** — small utilities: turning chunks into a context string,
  safely parsing JSON from the LLM, formatting file sizes.
- **exporters.py** — turns results into downloadable PDF / JSON / CSV bytes.

### `rag/` — the retrieval engine
- **embedding.py** — converts text into numeric vectors (meaning → numbers)
  using a free, local sentence-transformers model.
- **chunking.py** — splits long text into overlapping pieces. Two strategies:
  *Recursive* (fast, sentence-packed) and *Semantic* (topic-aware).
- **vector_store.py** — a thin wrapper around **ChromaDB**, the local vector
  database. Stores chunks + metadata and finds the closest ones to a query.
- **retrieval.py** — three search strategies: *Similarity* (closest),
  *MMR* (relevant **and** diverse, avoids repeats), *Hybrid* (vectors +
  keyword overlap so exact terms aren't missed).

### `services/` — the outside world
- **groq_service.py** — the **only** file that talks to the Groq API. It sends
  a system+user prompt and returns text, counting calls for monitoring.
- **pdf_service.py** — the **only** file that reads PDFs. Uses PyMuPDF for text/
  images/metadata and pdfplumber for tables. Handles empty/scanned PDFs safely.

### `agents/` — the reasoning layer
Each agent does one thing and returns clean data:
- **extraction_agent** — PDF → raw content → chunks → stored vectors.
- **retrieval_agent** — "get me the relevant chunks" (shared by everyone).
- **qa_agent** — grounded answers with citations (anti-hallucination).
- **summary_agent** — executive/detailed/section/takeaway summaries.
- **insight_agent** — risks/opportunities/compliance/trends.
- **recommendation_agent** — suggested questions + next actions (JSON).
- **router_agent** — coordinates all of the above; the UI only talks to this.

### `app.py` — the interface
Builds the sidebar (all the sliders/dropdowns) and seven tabs. It contains
almost no AI logic — it collects your choices into a `cfg` dict, calls the
Router, and displays what comes back. Long-lived objects (vector store, chat
history) live in `st.session_state` so they survive Streamlit's reruns.

---

## 4. Why this design is "enterprise-style"

- **Separation of concerns** — UI, orchestration, agents, RAG, and external
  services are all in different files. You can swap ChromaDB for Pinecone, or
  Groq for another provider, by editing one file.
- **Single points of contact** — only `groq_service.py` calls the LLM; only
  `pdf_service.py` reads PDFs. That makes changes and debugging predictable.
- **Grounded answers** — the QA agent is forced to cite sources and refuse when
  the context lacks an answer, reducing hallucination.
- **Configurable** — models, embeddings, chunking, and retrieval are all tunable
  from the UI without touching code.
