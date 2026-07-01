"""
utils/exporters.py
==================
WHY THIS FILE EXISTS:
    Users want to take results out of the app (a summary as PDF, a full report
    as JSON, a table as CSV). This file turns Python data into downloadable
    bytes that Streamlit's download_button can serve.

WHAT IT DOES:
    - to_pdf_bytes(): render text into a simple PDF using fpdf2.
    - to_json_bytes(): serialise a dict into JSON bytes.
    - to_csv_bytes(): turn a list of dicts into CSV bytes.

HOW IT CONNECTS:
    - app.py imports these to build download buttons in the Summary,
      Insights, and Monitoring tabs.
"""

import io
import json
import csv


def to_pdf_bytes(title: str, body: str) -> bytes:
    """Create a minimal, clean PDF from a title and body text."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _latin1(title))
    pdf.ln(4)

    # Body
    pdf.set_font("Helvetica", "", 11)
    for line in body.split("\n"):
        pdf.multi_cell(0, 7, _latin1(line) if line.strip() else " ")

    # fpdf2 returns a bytearray; wrap to bytes for Streamlit.
    return bytes(pdf.output())


def _latin1(text: str) -> str:
    """
    The core fpdf fonts only support latin-1. Replace characters that would
    crash encoding (emoji, smart quotes) with safe equivalents.
    """
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2022": "-", "\u2026": "...",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def to_json_bytes(data: dict) -> bytes:
    """Serialise a dictionary into pretty JSON bytes."""
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


def to_csv_bytes(rows: list[dict]) -> bytes:
    """Turn a list of dictionaries into CSV bytes (keys become headers)."""
    if not rows:
        return b""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")
