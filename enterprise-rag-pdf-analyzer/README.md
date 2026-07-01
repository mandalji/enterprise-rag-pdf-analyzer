# 📄 Enterprise Agentic RAG PDF Analyzer

An enterprise-style, fully open-source **Agentic RAG** platform for analysing PDFs.
Upload documents, chat with them, generate summaries, extract risk/compliance
insights, compare multiple documents, and export reports — all built with
**Python + Streamlit**, powered by **open-source LLMs on Groq**, free
**sentence-transformers** embeddings, and a local **ChromaDB** vector store.

> Built to run **entirely from GitHub + Streamlit Cloud** — no terminal, Docker,
> or local setup required.

---

## ✨ Features

- Multi-PDF upload with text, table, image, and metadata extraction
- Recursive **and** semantic chunking (configurable)
- Choice of embedding model (MiniLM / BGE)
- Similarity, **MMR**, and **Hybrid** retrieval
- Seven specialised agents coordinated by a **Router Agent**
- Document chat with conversation memory and **source citations**
- Executive / detailed / section / takeaway summaries
- Risk, opportunity, compliance, and trend insights
- Multi-document comparison (similarities, differences, contradictions)
- Auto-generated recommended questions
- System monitoring + CSV/JSON/PDF export

---

## 🧠 How it works (the pipeline)

```
User → Streamlit UI → Router Agent
                          ├── Extraction Agent → PDF parsing → Chunking
                          ├── Retrieval Agent  → Vector search (Chroma)
                          ├── QA Agent         → grounded answers + citations
                          ├── Summary Agent
                          ├── Insight Agent
                          └── Recommendation Agent
                                     ↓
                        Embeddings (sentence-transformers)
                                     ↓
                              Groq open-source LLM
```

See **ARCHITECTURE.md** for the full breakdown of every file.

---

## 🚀 Deploy in ~10 minutes (no terminal needed)

### Step 1 — Get a free Groq API key
1. Go to **https://console.groq.com** and sign in.
2. Open **API Keys → Create API Key**.
3. Copy the key (it starts with `gsk_...`). Keep it safe — you'll paste it later.

### Step 2 — Put this project in your GitHub
1. Create a free account at **https://github.com** if you don't have one.
2. Click **New repository** → name it `enterprise-rag-pdf-analyzer` → **Create**.
3. On the empty repo page, click **uploading an existing file**.
4. Drag in **all** the files/folders from this project (keep the folder
   structure). Commit the changes.
   - Tip: GitHub's web uploader accepts folders. Upload the whole
     `enterprise-rag-pdf-analyzer` contents so `app.py` sits at the repo root.
   - Do **not** upload a real `.env` file — only `.env.example` belongs in git.

### Step 3 — Deploy on Streamlit Cloud
1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**.
3. Select your repo, branch `main`, and set **Main file path** to `app.py`.
4. Click **Deploy**. The first build takes a few minutes (it downloads the
   embedding model on first run).

### Step 4 — Add your secret key
1. In your deployed app, open **⋮ (top-right) → Settings → Secrets**.
2. Paste exactly this (replace with your real key):
   ```toml
   GROQ_API_KEY = "gsk_your_real_groq_api_key_here"
   ```
3. Save. The app reloads and is ready.

### Step 5 — Use it
Upload a PDF in **Tab 1**, click **Process Documents**, then explore the
Chat, Summary, Insights, and Recommended tabs.

---

## 💻 (Optional) Run locally

If you ever want to run it on your own machine:
```bash
pip install -r requirements.txt
cp .env.example .env          # then paste your real key into .env
streamlit run app.py
```

---

## 🧾 Environment variables

| Variable        | Where to set it (cloud)        | Where to set it (local) |
|-----------------|--------------------------------|-------------------------|
| `GROQ_API_KEY`  | Settings → Secrets             | `.env` file             |

---

## 🛠️ Troubleshooting

See **TROUBLESHOOTING.md** for common issues (missing key, scanned PDFs,
build timeouts, memory limits).

---

## 📈 Roadmap

See **ROADMAP.md** for cost analysis and the production upgrade path.

---

## 📁 Project structure

```
enterprise-rag-pdf-analyzer/
├── app.py                     # Streamlit UI + entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── TROUBLESHOOTING.md
├── ROADMAP.md
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── assets/
├── config/
│   └── settings.py            # central configuration
├── agents/
│   ├── router_agent.py        # orchestrator
│   ├── extraction_agent.py
│   ├── retrieval_agent.py
│   ├── qa_agent.py
│   ├── summary_agent.py
│   ├── insight_agent.py
│   └── recommendation_agent.py
├── rag/
│   ├── embedding.py
│   ├── chunking.py
│   ├── vector_store.py
│   └── retrieval.py
├── services/
│   ├── groq_service.py
│   └── pdf_service.py
├── utils/
│   ├── logger.py
│   ├── prompts.py
│   ├── helpers.py
│   └── exporters.py
└── data/                      # local ChromaDB lives here (git-ignored)
```

## License
MIT — free to use, modify, and share.
