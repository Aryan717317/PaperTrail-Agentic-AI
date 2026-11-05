from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import get_settings


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load the embedding model locally (downloads model weights on first use)."""
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache
def get_vector_store() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_path,
    )


def add_chunks(chunks: list[dict]) -> None:
    from langchain_core.documents import Document

    docs = [Document(page_content=item["text"], metadata=item["metadata"]) for item in chunks]
    if docs:
        get_vector_store().add_documents(docs)


def search_chunks(question: str, k: int = 6, paper_ids: list[str] | None = None):
    store = get_vector_store()
    if paper_ids:
        where = {"paper_id": paper_ids[0]} if len(paper_ids) == 1 else {"paper_id": {"$in": paper_ids}}
        return store.similarity_search(question, k=k, filter=where)
    return store.similarity_search(question, k=k)
