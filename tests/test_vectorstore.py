import os
import shutil
import tempfile
import pytest
from app.config import Settings
from app.embeddings.model import get_embeddings
from app.vectorstore.chroma_store import add_chunks, list_documents, delete_document


@pytest.fixture
def temp_chroma_env(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    test_settings = Settings(
        chroma_path=temp_dir,
        collection_name="test_papertrail",
    )
    monkeypatch.setattr("app.vectorstore.chroma_store.get_settings", lambda: test_settings)
    monkeypatch.setattr("app.config.get_settings", lambda: test_settings)
    
    # Clear vectorstore cache so it uses test settings
    from app.vectorstore.chroma_store import get_vector_store
    get_vector_store.cache_clear()
    
    yield temp_dir
    
    get_vector_store.cache_clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_add_chunks_and_deduplication(temp_chroma_env):
    chunks = [
        {
            "text": "Chunk text number 1 about attention mechanisms.",
            "metadata": {
                "paper_id": "p1",
                "filename": "paper1.pdf",
                "page": 1,
                "chunk_id": "p1-0001-abc",
            },
        },
        {
            "text": "Chunk text number 2 about loss functions.",
            "metadata": {
                "paper_id": "p1",
                "filename": "paper1.pdf",
                "page": 2,
                "chunk_id": "p1-0002-def",
            },
        },
    ]

    # First add: 2 added
    added = add_chunks(chunks)
    assert added == 2

    # Second add with same chunk_ids: 0 added (deduplication works)
    added_again = add_chunks(chunks)
    assert added_again == 0

    # List documents
    docs = list_documents()
    assert len(docs) == 1
    assert docs[0]["paper_id"] == "p1"
    assert docs[0]["chunk_count"] == 2

    # Delete document
    deleted = delete_document("p1")
    assert deleted == 2
    assert len(list_documents()) == 0
