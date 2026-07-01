# 🛠️ Troubleshooting Guide

### "No Groq API key found"
The app can't see your key.
- **Cloud:** Settings → Secrets must contain `GROQ_API_KEY = "gsk_..."` (with quotes). Save, then let the app reload.
- **Local:** you must have a `.env` file (not `.env.example`) with `GROQ_API_KEY=gsk_...`.

### The app builds but errors on first question
The embedding model downloads on first use. Wait for it, or process a document first (which triggers the download during a spinner).

### "No selectable text found / scanned PDF"
Your PDF is a scanned image with no text layer. This MVP does not include OCR. Use a text-based PDF, or add OCR later (see ROADMAP.md).

### Streamlit Cloud build times out or runs out of memory
The free tier has ~1 GB RAM. Tips:
- Use the smaller embedding model (**all-MiniLM-L6-v2**).
- Upload smaller/fewer PDFs at once.
- Keep `Max Tokens` moderate (1024).
- If a build hangs, reboot the app from the Streamlit dashboard.

### ChromaDB / sqlite errors on Streamlit Cloud
Ensure `chromadb` is in requirements.txt (it is). If you see an sqlite version error, it usually resolves on a fresh reboot because the pinned chromadb version bundles a compatible backend.

### Answers seem to ignore my document
- Confirm the file processed (Tab 1 shows chunk count > 0).
- Increase **Top-K** (chunks retrieved) in the sidebar.
- Try **Hybrid** search for exact terms like names or codes.

### Tables/images look empty
Not all PDFs contain extractable tables or embedded images. Tables come from pdfplumber and only appear when the PDF has real table structures.

### Import errors after editing code
Check that every folder still has its `__init__.py` file and that `app.py` is at the repository root (same level as `requirements.txt`).

### Rate limits from Groq
Free Groq usage has per-minute limits. If you hit them, wait a minute or switch to the faster/smaller model (Llama 3.1 8B).
