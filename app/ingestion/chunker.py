"""
app/ingestion/chunker.py

Splits cleaned page text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter, which respects paragraph and sentence
boundaries rather than cutting on raw character counts.

Each chunk dict produced here matches the shape expected by
app.vectorstore.chroma_store.add_chunks():

    {
        "text": str,
        "metadata": {
            "paper_id": str,
            "filename": str,
            "page": int,
            "chunk_id": str,   # sha256-based deduplication key
        },
    }
"""

import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter


def _make_chunk_id(paper_id: str, page: int, text: str) -> str:
    """
    Deterministic chunk identifier based on content.
    Two identical passages in the same paper/page get the same ID, which
    allows duplicate-chunk detection later.
    """
    digest = hashlib.sha256(f"{paper_id}:{page}:{text}".encode()).hexdigest()[:16]
    return f"{paper_id[:8]}-p{page:04d}-{digest}"


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1200,
    chunk_overlap: int = 180,
) -> list[dict]:
    """
    Convert a list of page dicts into a flat list of chunk dicts.

    Parameters
    ----------
    pages : list[dict]
        Output of app.ingestion.pdf_extractor.extract_pages(), optionally
        cleaned by app.ingestion.cleaner.clean_text().
    chunk_size : int
        Maximum number of characters per chunk.
    chunk_overlap : int
        Number of characters of overlap between consecutive chunks.

    Returns
    -------
    list[dict]
        Flat list of chunk dicts with text + metadata.

    Raises
    ------
    ValueError
        On invalid chunking parameters.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must satisfy 0 <= chunk_overlap < chunk_size.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # Try to split on paragraph breaks, then sentences, then words.
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[dict] = []
    for page in pages:
        text = page.get("text", "")
        if not isinstance(text, str):
            raise ValueError("Each page dict must contain 'text' as a string.")
        text = text.strip()
        if not text:
            continue

        paper_id: str = page["paper_id"]
        filename: str = page["filename"]
        page_num: int = int(page["page"])

        for fragment in splitter.split_text(text):
            fragment = fragment.strip()
            if not fragment:
                continue
            chunks.append(
                {
                    "text": fragment,
                    "metadata": {
                        "paper_id": paper_id,
                        "filename": filename,
                        "page": page_num,
                        "chunk_id": _make_chunk_id(paper_id, page_num, fragment),
                    },
                }
            )

    return chunks

