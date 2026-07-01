"""
agents/extraction_agent.py
==========================
WHY THIS FILE EXISTS:
    This agent owns the first stage of the pipeline: turning an uploaded PDF
    into searchable knowledge. It coordinates the PDF service (raw extraction),
    the chunker (splitting), and the vector store (embedding + storage).

WHAT IT DOES:
    - Calls services/pdf_service.extract_pdf() to get raw content.
    - Chunks each page's text using rag/chunking.
    - Stores chunks (with filename + page metadata) in the vector store.
    - Returns a per-file report used by the UI (pages, tables, images, chunks).

HOW IT CONNECTS:
    - Called by the Router Agent when the user uploads documents.
    - Feeds the vector store that every other agent later reads from.
"""

from services.pdf_service import extract_pdf
from rag.chunking import chunk_text
from utils.logger import log


def run(file_bytes, filename, store, settings_dict) -> dict:
    """
    Process one PDF end to end.
    settings_dict carries the UI choices: chunk_strategy, chunk_size,
    chunk_overlap, embedding_model.
    """
    extracted = extract_pdf(file_bytes, filename)

    report = {
        "filename": filename,
        "num_pages": extracted["num_pages"],
        "num_tables": len(extracted["tables"]),
        "num_images": len(extracted["images"]),
        "chunks_created": 0,
        "metadata": extracted["metadata"],
        "pages": extracted["pages"],
        "tables": extracted["tables"],
        "images": extracted["images"],
        "error": extracted["error"],
    }

    if extracted["error"]:
        log(f"Extraction stopped for {filename}: {extracted['error']}", "WARN")
        return report

    # Chunk each page and store, keeping page numbers for citations.
    total_chunks = 0
    for page in extracted["pages"]:
        if not page["text"]:
            continue
        chunks = chunk_text(
            text=page["text"],
            strategy=settings_dict["chunk_strategy"],
            chunk_size=settings_dict["chunk_size"],
            overlap=settings_dict["chunk_overlap"],
            embedding_model=settings_dict["embedding_model"],
        )
        if chunks:
            store.add_chunks(
                chunks,
                base_metadata={"filename": filename, "page": page["page"]},
            )
            total_chunks += len(chunks)

    report["chunks_created"] = total_chunks
    log(f"Extraction agent finished {filename}: {total_chunks} chunks")
    return report
