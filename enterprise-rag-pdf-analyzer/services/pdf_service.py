"""
services/pdf_service.py
=======================
WHY THIS FILE EXISTS:
    Before we can analyse a PDF we must pull the raw content out of it: the
    text on each page, any tables, any images, and the document's metadata.
    This file does exactly that using two complementary libraries.

WHAT IT DOES:
    - Uses PyMuPDF (imported as 'fitz') for fast text, metadata, and images.
    - Uses pdfplumber for reliable table extraction.
    - Returns a clean dictionary the extraction agent can work with.
    - Handles empty or corrupted PDFs without crashing the app.

HOW IT CONNECTS:
    - agents/extraction_agent.py calls extract_pdf() for each uploaded file.
    - app.py's Document Explorer tab displays what this returns.

INPUT:  raw PDF bytes + filename
OUTPUT: {
    "filename": str,
    "metadata": dict,
    "pages": [{"page": int, "text": str}],
    "tables": [{"page": int, "rows": [[...]]}],
    "images": [{"page": int, "bytes": b"...", "ext": "png"}],
    "num_pages": int,
    "error": str | None,
}
"""

import io
from utils.logger import log


def extract_pdf(file_bytes: bytes, filename: str) -> dict:
    """Extract text, tables, images, and metadata from PDF bytes."""
    result = {
        "filename": filename,
        "metadata": {},
        "pages": [],
        "tables": [],
        "images": [],
        "num_pages": 0,
        "error": None,
    }

    if not file_bytes:
        result["error"] = "The file is empty."
        return result

    # --- TEXT, METADATA, IMAGES via PyMuPDF --------------------------------
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        result["num_pages"] = doc.page_count
        result["metadata"] = {
            k: v for k, v in (doc.metadata or {}).items() if v
        }

        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            text = page.get_text("text") or ""
            result["pages"].append({"page": page_index + 1, "text": text.strip()})

            # Extract embedded images (limit to a few per page to stay light).
            for img in page.get_images(full=True)[:3]:
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:  # CMYK -> convert to RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    result["images"].append(
                        {"page": page_index + 1, "bytes": pix.tobytes("png"), "ext": "png"}
                    )
                    pix = None
                except Exception:
                    continue
        doc.close()
    except Exception as exc:
        result["error"] = f"Could not read PDF text: {exc}"
        log(f"PyMuPDF failed on {filename}: {exc}", "ERROR")
        return result

    # --- TABLES via pdfplumber --------------------------------------------
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                for table in page.extract_tables() or []:
                    cleaned = [
                        [("" if cell is None else str(cell)) for cell in row]
                        for row in table
                    ]
                    if cleaned:
                        result["tables"].append({"page": i + 1, "rows": cleaned})
    except Exception as exc:
        # Tables are a bonus; don't fail the whole extraction if this breaks.
        log(f"pdfplumber tables skipped for {filename}: {exc}", "WARN")

    # --- SANITY CHECK ------------------------------------------------------
    all_text = " ".join(p["text"] for p in result["pages"]).strip()
    if not all_text:
        result["error"] = (
            "No selectable text found. This PDF may be a scanned image "
            "(OCR would be required, which this MVP does not include)."
        )

    log(
        f"Extracted {filename}: {result['num_pages']} pages, "
        f"{len(result['tables'])} tables, {len(result['images'])} images"
    )
    return result
