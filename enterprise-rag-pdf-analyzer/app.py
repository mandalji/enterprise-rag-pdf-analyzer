"""
app.py
======
WHY THIS FILE EXISTS:
    This is the entry point Streamlit runs. It builds the entire user interface
    (sidebar + 7 tabs) and connects every button to the Router Agent. It holds
    almost no AI logic itself — it just collects settings, calls the Router,
    and displays results. That separation is what makes the project modular.

WHAT IT DOES:
    - Builds the sidebar (branding, model settings, retrieval settings, about).
    - Creates the shared VectorStore and RouterAgent (once per session).
    - Renders 7 tabs: Upload, Explorer, Chat, Summary, Insights,
      Recommended Questions, System Monitoring.
    - Handles downloads/exports and chat memory.

HOW IT CONNECTS:
    - Imports config/settings for all defaults & option lists.
    - Talks only to agents/router_agent.RouterAgent for AI work.
    - Uses utils/ (logger, helpers, exporters) for supporting features.

RUN LOCALLY:  streamlit run app.py
"""

import time
import streamlit as st

from config import settings
from agents.router_agent import RouterAgent
from rag.vector_store import VectorStore
from services.groq_service import GroqError
from utils import logger, exporters
from utils.helpers import human_size

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# SESSION STATE INITIALISATION
# Streamlit reruns this whole file on every interaction, so we keep long-lived
# objects (vector store, chat history, processed files) in st.session_state.
# ---------------------------------------------------------------------------
def init_state(embedding_model):
    if "store" not in st.session_state or st.session_state.get("emb") != embedding_model:
        st.session_state.store = VectorStore(embedding_model)
        st.session_state.emb = embedding_model
    if "router" not in st.session_state or st.session_state.get("emb_r") != embedding_model:
        st.session_state.router = RouterAgent(st.session_state.store)
        st.session_state.emb_r = embedding_model
    st.session_state.setdefault("chat", [])          # list of {q, a, sources}
    st.session_state.setdefault("reports", [])        # per-file extraction reports
    st.session_state.setdefault("api_calls", 0)
    st.session_state.setdefault("proc_time", 0.0)
    st.session_state.setdefault("recommended", None)


# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
def build_sidebar():
    with st.sidebar:
        # --- Branding ---
        st.markdown("## 📄 " + settings.APP_TITLE)
        st.caption("Agentic RAG • Groq • ChromaDB")
        st.divider()

        # --- Model Settings ---
        st.markdown("### ⚙️ Model Settings")
        model_label = st.selectbox("Model", list(settings.GROQ_MODELS.keys()),
                                   index=list(settings.GROQ_MODELS).index(settings.DEFAULT_MODEL_LABEL))
        temperature = st.slider("Temperature", 0.0, 1.0, settings.DEFAULT_TEMPERATURE, 0.05)
        top_p = st.slider("Top-P", 0.0, 1.0, settings.DEFAULT_TOP_P, 0.05)
        max_tokens = st.slider("Max Tokens", 256, 4096, settings.DEFAULT_MAX_TOKENS, 128)

        st.divider()

        # --- Embedding + Retrieval Settings ---
        st.markdown("### 🔎 Retrieval Settings")
        emb_label = st.selectbox("Embedding Model", list(settings.EMBEDDING_MODELS.keys()),
                                 index=list(settings.EMBEDDING_MODELS).index(settings.DEFAULT_EMBEDDING_LABEL))
        chunk_strategy = st.selectbox("Chunking", settings.CHUNK_STRATEGIES)
        chunk_size = st.slider("Chunk Size (chars)", 300, 1500, settings.DEFAULT_CHUNK_SIZE, 50)
        chunk_overlap = st.slider("Chunk Overlap (chars)", 0, 400, settings.DEFAULT_CHUNK_OVERLAP, 20)
        search_type = st.selectbox("Search Type", settings.SEARCH_TYPES)
        top_k = st.slider("Chunks Retrieved (Top-K)", 1, 10, settings.DEFAULT_TOP_K)

        st.divider()

        # --- About ---
        with st.expander("ℹ️ About"):
            st.write(f"**Version:** {settings.APP_VERSION}")
            st.write(settings.DEVELOPER)
            st.write("An enterprise-style Agentic RAG platform for analysing PDFs.")

        # API key warning
        if not settings.GROQ_API_KEY:
            st.error("⚠️ No Groq API key found. Add it in Settings → Secrets "
                     "(cloud) or a local .env file.")

    return {
        "model_label": model_label,
        "model": settings.GROQ_MODELS[model_label],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "embedding_model": settings.EMBEDDING_MODELS[emb_label],
        "chunk_strategy": chunk_strategy,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "search_type": search_type,
        "top_k": top_k,
    }


# ---------------------------------------------------------------------------
# TAB 1 — DOCUMENT UPLOAD
# ---------------------------------------------------------------------------
def tab_upload(cfg):
    st.subheader("📤 Document Upload")
    files = st.file_uploader("Upload one or more PDFs", type=["pdf"],
                             accept_multiple_files=True)

    if files and st.button("Process Documents", type="primary"):
        processed_names = {r["filename"] for r in st.session_state.reports}
        start = time.time()
        for f in files:
            if f.name in processed_names:
                st.info(f"Skipping already-processed file: {f.name}")
                continue
            with st.spinner(f"Processing {f.name}…"):
                try:
                    report = st.session_state.router.ingest(f.getvalue(), f.name, cfg)
                    st.session_state.reports.append(report)
                    if report["error"]:
                        st.warning(f"{f.name}: {report['error']}")
                    else:
                        st.success(
                            f"{f.name}: {report['num_pages']} pages, "
                            f"{report['chunks_created']} chunks, "
                            f"{report['num_tables']} tables, "
                            f"{report['num_images']} images."
                        )
                except Exception as exc:
                    st.error(f"Failed to process {f.name}: {exc}")
        st.session_state.proc_time += time.time() - start
        st.session_state.recommended = None  # force regen next time

    # File information table
    if st.session_state.reports:
        st.markdown("#### Processed Files")
        st.dataframe(
            [
                {
                    "File": r["filename"],
                    "Pages": r["num_pages"],
                    "Chunks": r["chunks_created"],
                    "Tables": r["num_tables"],
                    "Images": r["num_images"],
                    "Status": "Error" if r["error"] else "OK",
                }
                for r in st.session_state.reports
            ],
            use_container_width=True, hide_index=True,
        )

    # Processing logs
    with st.expander("📜 Processing Logs"):
        st.code("\n".join(logger.get_logs()[-100:]) or "No logs yet.")


# ---------------------------------------------------------------------------
# TAB 2 — DOCUMENT EXPLORER
# ---------------------------------------------------------------------------
def tab_explorer():
    st.subheader("🔍 Document Explorer")
    if not st.session_state.reports:
        st.info("Upload and process a document first.")
        return

    names = [r["filename"] for r in st.session_state.reports]
    choice = st.selectbox("Select a document", names)
    report = next(r for r in st.session_state.reports if r["filename"] == choice)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Metadata**")
        st.json(report["metadata"] or {"info": "No metadata found."})
    with c2:
        st.markdown("**Overview**")
        st.write(f"Pages: {report['num_pages']}")
        st.write(f"Tables: {report['num_tables']}")
        st.write(f"Images: {report['num_images']}")

    # Page viewer
    if report["pages"]:
        page_no = st.number_input("View page", 1, max(report["num_pages"], 1), 1)
        page = next((p for p in report["pages"] if p["page"] == page_no), None)
        st.text_area("Page text", page["text"] if page else "", height=250)

    # Tables
    if report["tables"]:
        st.markdown("**Extracted Tables**")
        for i, tbl in enumerate(report["tables"][:10]):
            st.caption(f"Table {i+1} (page {tbl['page']})")
            st.table(tbl["rows"][:15])

    # Images
    if report["images"]:
        st.markdown("**Extracted Images**")
        cols = st.columns(3)
        for i, img in enumerate(report["images"][:9]):
            with cols[i % 3]:
                st.image(img["bytes"], caption=f"Page {img['page']}", use_container_width=True)


# ---------------------------------------------------------------------------
# TAB 3 — DOCUMENT CHAT
# ---------------------------------------------------------------------------
def tab_chat(cfg):
    st.subheader("💬 Document Chat")
    if st.session_state.store.count() == 0:
        st.info("Upload and process a document first.")
        return

    # Show history
    for turn in st.session_state.chat:
        with st.chat_message("user"):
            st.write(turn["q"])
        with st.chat_message("assistant"):
            st.write(turn["a"])
            if turn["sources"]:
                with st.expander("Sources"):
                    for s in turn["sources"]:
                        st.caption(f"{s['filename']} • page {s['page']} • chunk {s['chunk_id']}")

    question = st.chat_input("Ask a question about your documents…")
    if question:
        # Build short history string for memory.
        history_text = "\n".join(
            f"User: {t['q']}\nAssistant: {t['a']}" for t in st.session_state.chat[-3:]
        )
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    result = st.session_state.router.ask(question, cfg, history_text)
                    st.write(result["answer"])
                    if result["sources"]:
                        with st.expander("Sources"):
                            for s in result["sources"]:
                                st.caption(f"{s['filename']} • page {s['page']} • chunk {s['chunk_id']}")
                    st.session_state.chat.append(
                        {"q": question, "a": result["answer"], "sources": result["sources"]}
                    )
                except GroqError as exc:
                    st.error(str(exc))

    if st.session_state.chat and st.button("Clear conversation"):
        st.session_state.chat = []
        st.rerun()


# ---------------------------------------------------------------------------
# TAB 4 — EXECUTIVE SUMMARY
# ---------------------------------------------------------------------------
def tab_summary(cfg):
    st.subheader("📝 Executive Summary")
    if st.session_state.store.count() == 0:
        st.info("Upload and process a document first.")
        return

    mode = st.radio("Summary type", ["Executive", "Detailed", "Section", "Takeaways"],
                    horizontal=True)
    if st.button("Generate Summary", type="primary"):
        with st.spinner("Summarising…"):
            try:
                summary = st.session_state.router.summarise(mode, cfg)
                st.session_state.last_summary = summary
            except GroqError as exc:
                st.error(str(exc))

    if st.session_state.get("last_summary"):
        st.markdown(st.session_state.last_summary)
        st.download_button(
            "⬇️ Download as PDF",
            data=exporters.to_pdf_bytes("Document Summary", st.session_state.last_summary),
            file_name="summary.pdf", mime="application/pdf",
        )


# ---------------------------------------------------------------------------
# TAB 5 — ENTERPRISE INSIGHTS
# ---------------------------------------------------------------------------
def tab_insights(cfg):
    st.subheader("📊 Enterprise Insights")
    if st.session_state.store.count() == 0:
        st.info("Upload and process a document first.")
        return

    focus = st.selectbox("Analysis focus", ["Risks", "Opportunities", "Compliance", "Trends"])
    multi = [r["filename"] for r in st.session_state.reports if not r["error"]]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Analysis", type="primary"):
            with st.spinner("Analysing…"):
                try:
                    st.session_state.last_insight = st.session_state.router.insight(focus, cfg)
                except GroqError as exc:
                    st.error(str(exc))
    with col2:
        if len(multi) >= 2 and st.button("Compare Documents"):
            with st.spinner("Comparing…"):
                try:
                    st.session_state.last_insight = st.session_state.router.compare(cfg, multi)
                except GroqError as exc:
                    st.error(str(exc))

    if st.session_state.get("last_insight"):
        st.markdown(st.session_state.last_insight)
        st.download_button(
            "⬇️ Download as JSON",
            data=exporters.to_json_bytes({"analysis": st.session_state.last_insight}),
            file_name="insights.json", mime="application/json",
        )


# ---------------------------------------------------------------------------
# TAB 6 — RECOMMENDED QUESTIONS
# ---------------------------------------------------------------------------
def tab_recommended(cfg):
    st.subheader("💡 Recommended Questions")
    if st.session_state.store.count() == 0:
        st.info("Upload and process a document first.")
        return

    if st.session_state.recommended is None:
        if st.button("Generate Recommendations", type="primary"):
            with st.spinner("Thinking of good questions…"):
                try:
                    st.session_state.recommended = st.session_state.router.recommend(cfg)
                except GroqError as exc:
                    st.error(str(exc))

    rec = st.session_state.recommended
    if rec:
        st.markdown("**Suggested questions** (click to ask in the Chat tab):")
        for q in rec.get("questions", []):
            if st.button(f"❓ {q}", key=f"rq_{q}"):
                history_text = ""
                with st.spinner("Answering…"):
                    try:
                        result = st.session_state.router.ask(q, cfg, history_text)
                        st.session_state.chat.append(
                            {"q": q, "a": result["answer"], "sources": result["sources"]}
                        )
                        st.success("Answer added to the Chat tab.")
                        st.markdown(result["answer"])
                    except GroqError as exc:
                        st.error(str(exc))
        st.markdown("**Recommended next actions:**")
        for a in rec.get("actions", []):
            st.write(f"- {a}")


# ---------------------------------------------------------------------------
# TAB 7 — SYSTEM MONITORING
# ---------------------------------------------------------------------------
def tab_monitoring():
    st.subheader("📈 System Monitoring")
    stats = st.session_state.store.stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Files", len(stats["files"]))
    c2.metric("Chunks / Vectors", stats["total_chunks"])
    c3.metric("API Calls", st.session_state.api_calls)
    c4.metric("Processing Time", f"{st.session_state.proc_time:.1f}s")

    if stats["files"]:
        st.markdown("**Uploaded files:**")
        for f in stats["files"]:
            st.write(f"- {f}")

    # Export a CSV report of processed files.
    if st.session_state.reports:
        rows = [
            {
                "filename": r["filename"], "pages": r["num_pages"],
                "chunks": r["chunks_created"], "tables": r["num_tables"],
                "images": r["num_images"], "status": "error" if r["error"] else "ok",
            }
            for r in st.session_state.reports
        ]
        st.download_button(
            "⬇️ Download report (CSV)",
            data=exporters.to_csv_bytes(rows),
            file_name="report.csv", mime="text/csv",
        )

    st.divider()
    if st.button("🗑️ Clear ALL data", type="secondary"):
        st.session_state.store.reset()
        st.session_state.reports = []
        st.session_state.chat = []
        st.session_state.recommended = None
        logger.clear_logs()
        st.success("All data cleared.")
        st.rerun()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    cfg = build_sidebar()
    init_state(cfg["embedding_model"])

    st.title("📄 Enterprise Agentic RAG PDF Analyzer")
    st.caption("Upload PDFs → chat, summarise, and extract enterprise insights.")

    tabs = st.tabs([
        "1 · Upload", "2 · Explorer", "3 · Chat", "4 · Summary",
        "5 · Insights", "6 · Recommended", "7 · Monitoring",
    ])
    with tabs[0]: tab_upload(cfg)
    with tabs[1]: tab_explorer()
    with tabs[2]: tab_chat(cfg)
    with tabs[3]: tab_summary(cfg)
    with tabs[4]: tab_insights(cfg)
    with tabs[5]: tab_recommended(cfg)
    with tabs[6]: tab_monitoring()


if __name__ == "__main__":
    main()
