"""
app/ingestion/pdf_extractor.py

Extracts text page-by-page from text-based PDFs using PyMuPDF.
Scanned / image-only PDFs are rejected with a clear message (OCR is out of scope for MVP).
"""

from uuid import uuid4
import pymupdf


def extract_pages(pdf_path: str, filename: str) -> tuple[str, list[dict]]:
    """
    Open a PDF and extract text from every page that has selectable content.
    """
    paper_id = str(uuid4())
    pages: list[dict] = []

    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()
            if text:
                pages.append(
                    {
                        "paper_id": paper_id,
                        "filename": filename,
                        "page": page_number,
                        "text": text,
                    }
                )

    if not pages:
        raise ValueError(
            "No selectable text was found in this PDF. "
            "It may be a scanned document; OCR is not supported in this version."
        )

    return paper_id, pages
