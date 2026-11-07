"""
app/services/document_service.py

High-level document lifecycle service: ingestion, listing, and deletion.
"""

import logging
import os
import tempfile
from fastapi import UploadFile

from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_extractor import extract_pages
from app.schemas import DocumentInfo, DocumentListResponse, UploadResponse
from app.vectorstore.chroma_store import add_chunks, delete_document, list_documents

logger = logging.getLogger(__name__)

MAX_PDF_BYTES = 25 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024


def process_and_index_pdf(pdf_path: str, filename: str) -> UploadResponse:
    """
    Extract, clean, chunk, and index a PDF file from a local filesystem path.
    """
    paper_id, raw_pages = extract_pages(pdf_path, filename)
    
    # Clean text page-by-page
    cleaned_pages = []
    for p in raw_pages:
        cleaned_pages.append({
            "paper_id": p["paper_id"],
            "filename": p["filename"],
            "page": p["page"],
            "text": clean_text(p["text"]),
        })

    # Chunk cleaned pages
    chunks = chunk_pages(cleaned_pages)
    
    # Add to persistent vectorstore
    chunks_added = add_chunks(chunks)

    return UploadResponse(
        paper_id=paper_id,
        filename=filename,
        pages_extracted=len(raw_pages),
        chunks_indexed=chunks_added,
        status="indexed",
    )


async def handle_uploaded_file(file: UploadFile) -> UploadResponse:
    """
    Stream uploaded file to a temporary file, validate size, and index it.
    """
    filename = file.filename or "uploaded.pdf"
    temp_path = None
    total_bytes = 0

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            while True:
                chunk = await file.read(UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_PDF_BYTES:
                    raise ValueError("Maximum PDF size is 25 MB.")
                tmp.write(chunk)

        if total_bytes == 0:
            raise ValueError("The uploaded file is empty.")

        return process_and_index_pdf(temp_path, filename)
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def get_all_documents() -> DocumentListResponse:
    """List all indexed documents in the system."""
    docs = list_documents()
    items = [
        DocumentInfo(
            paper_id=d["paper_id"],
            filename=d["filename"],
            chunk_count=d["chunk_count"],
        )
        for d in docs
    ]
    return DocumentListResponse(total_documents=len(items), documents=items)


def remove_document(paper_id: str) -> int:
    """Delete all chunks for a given paper."""
    return delete_document(paper_id)
