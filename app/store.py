"""
app/store.py

Backward-compatible facade delegating to the modular vectorstore & embeddings packages.
"""

from app.embeddings.model import get_embeddings
from app.vectorstore.chroma_store import (
    add_chunks,
    delete_document,
    get_vector_store,
    list_documents,
    search_chunks,
)

__all__ = [
    "get_embeddings",
    "get_vector_store",
    "add_chunks",
    "search_chunks",
    "list_documents",
    "delete_document",
]
