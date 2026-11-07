"""
app/vectorstore/chroma_store.py

Thin wrapper around LangChain's Chroma integration.

Responsibilities
----------------
- Provide a singleton Chroma vector store (get_vector_store).
- Add document chunks (add_chunks) with duplicate detection via chunk_id.
- Perform semantic similarity search (search_chunks) with optional
  paper_id filtering.
- List all indexed documents (list_documents).
- Delete all chunks belonging to a document (delete_document).
"""

import logging
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import get_settings
from app.embeddings.model import get_embeddings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    """
    Return the persistent Chroma vector store singleton.

    The store is backed by the directory specified in Settings.chroma_path
    (default: data/chroma).  The directory is created automatically on first
    use.
    """
    settings = get_settings()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_path,
    )


def add_chunks(chunks: list[dict]) -> int:
    """
    Embed and store a list of chunk dicts.

    Duplicate chunks (same chunk_id) are skipped so that re-uploading the
    same paper does not create duplicate entries.

    Parameters
    ----------
    chunks : list[dict]
        Output of app.ingestion.chunker.chunk_pages().

    Returns
    -------
    int
        Number of *new* chunks actually added (excluding duplicates).
    """
    if not chunks:
        return 0

    store = get_vector_store()

    # Fetch existing chunk_ids to avoid duplicates.
    existing_ids: set[str] = set()
    try:
        collection = store._collection  # type: ignore[attr-defined]
        result = collection.get(include=[])
        existing_ids = set(result.get("ids", []))
    except Exception:
        logger.debug("Could not fetch existing IDs from ChromaDB; proceeding without dedup.")

    new_docs: list[Document] = []
    new_ids: list[str] = []

    for item in chunks:
        chunk_id: str = item["metadata"].get("chunk_id", "")
        if chunk_id and chunk_id in existing_ids:
            continue
        new_docs.append(Document(page_content=item["text"], metadata=item["metadata"]))
        if chunk_id:
            new_ids.append(chunk_id)

    if new_docs:
        if new_ids and len(new_ids) == len(new_docs):
            store.add_documents(new_docs, ids=new_ids)
        else:
            store.add_documents(new_docs)

    added = len(new_docs)
    skipped = len(chunks) - added
    if skipped:
        logger.info("Skipped %d duplicate chunks.", skipped)
    return added


def search_chunks(
    question: str,
    k: int = 6,
    paper_ids: list[str] | None = None,
) -> list[Document]:
    """
    Retrieve the top-k semantically relevant chunks for a question.

    Parameters
    ----------
    question : str
        The user's research question.
    k : int
        Number of chunks to retrieve.
    paper_ids : list[str] | None
        If supplied, restrict retrieval to chunks belonging to those papers.

    Returns
    -------
    list[Document]
        LangChain Document objects with page_content and metadata.
    """
    store = get_vector_store()
    where: dict | None = None
    if paper_ids:
        where = (
            {"paper_id": paper_ids[0]}
            if len(paper_ids) == 1
            else {"paper_id": {"$in": paper_ids}}
        )
    return store.similarity_search(question, k=k, filter=where)


def list_documents() -> list[dict]:
    """
    Return one summary dict per unique paper in the store.

    Returns
    -------
    list[dict]
        [{"paper_id": str, "filename": str, "chunk_count": int}, ...]
    """
    store = get_vector_store()
    try:
        collection = store._collection  # type: ignore[attr-defined]
        result = collection.get(include=["metadatas"])
    except Exception:
        return []

    seen: dict[str, dict] = {}
    for meta in result.get("metadatas") or []:
        pid = meta.get("paper_id", "")
        if pid not in seen:
            seen[pid] = {
                "paper_id": pid,
                "filename": meta.get("filename", "Unknown"),
                "chunk_count": 0,
            }
        seen[pid]["chunk_count"] += 1

    return list(seen.values())


def delete_document(paper_id: str) -> int:
    """
    Delete all chunks belonging to a given paper_id.

    Parameters
    ----------
    paper_id : str
        The UUID assigned at upload time.

    Returns
    -------
    int
        Number of chunks deleted.
    """
    store = get_vector_store()
    try:
        collection = store._collection  # type: ignore[attr-defined]
        result = collection.get(where={"paper_id": paper_id}, include=[])
        ids = result.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception as exc:
        logger.error("Failed to delete paper %s: %s", paper_id, exc)
        return 0

