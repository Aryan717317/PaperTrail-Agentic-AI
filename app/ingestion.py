"""
app/ingestion.py

Backward-compatible facade delegating to the modular ingestion package.
"""

from app.ingestion.pdf_extractor import extract_pages
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_pages

__all__ = ["extract_pages", "clean_text", "chunk_pages"]
