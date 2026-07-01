# 📈 Cost Analysis & Production Upgrade Roadmap

## 💰 Cost analysis (this MVP)

| Component            | Choice                         | Cost           |
|---------------------|--------------------------------|----------------|
| Hosting             | Streamlit Community Cloud      | **Free**       |
| LLM                 | Open-source models on Groq     | **Free tier**  |
| Embeddings          | sentence-transformers (local)  | **Free**       |
| Vector DB           | ChromaDB (local/embedded)      | **Free**       |
| PDF parsing         | PyMuPDF + pdfplumber           | **Free**       |
| **Total**           |                                | **$0 to run**  |

The only limits are the free tiers: Groq per-minute rate limits and Streamlit
Cloud's ~1 GB RAM / sleep-on-idle behaviour.

## 🚀 Production upgrade roadmap

### Stage 1 — Harden the MVP
- Add user authentication (Streamlit-Authenticator or an SSO proxy).
- Persist ChromaDB to durable storage (it resets when the free app sleeps).
- Add OCR for scanned PDFs (Tesseract or a cloud OCR API).
- Add unit tests for chunking, retrieval, and exporters.

### Stage 2 — Scale the RAG
- Move to a managed vector DB (Pinecone, Weaviate, Qdrant, or pgvector).
- Add re-ranking (e.g. a cross-encoder) after retrieval for better precision.
- Cache embeddings and LLM responses to cut latency and rate-limit pressure.
- Introduce async ingestion for large document batches.

### Stage 3 — Enterprise features
- Role-based access control and per-tenant document isolation.
- Audit logging and PII redaction before storage.
- Observability: latency, token usage, and cost dashboards.
- Human-in-the-loop review for high-stakes insights.

### Stage 4 — Deployment maturity
- Containerise with Docker and deploy to a managed platform (Cloud Run, ECS, AKS).
- CI/CD via GitHub Actions (lint, test, deploy).
- Secrets in a vault (AWS Secrets Manager / Azure Key Vault), not app settings.
- Autoscaling + a separate worker service for heavy ingestion jobs.

### Stage 5 — Advanced agentic capabilities
- A planning agent that decomposes complex queries into sub-tasks.
- Tool-use agents (web search, database lookups) alongside document RAG.
- Long-term memory across sessions per user.
- Evaluation harness to measure answer faithfulness and citation accuracy.
