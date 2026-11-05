import pytest
from app.ingestion import chunk_pages


def test_chunk_pages_preserves_page_metadata():
    pages = [{
        "paper_id": "p1",
        "filename": "sample.pdf",
        "page": 4,
        "text": "A" * 2500,
    }]
    chunks = chunk_pages(pages, chunk_size=1000, overlap=100)

    assert len(chunks) == 3
    assert all(chunk["metadata"]["paper_id"] == "p1" for chunk in chunks)
    assert all(chunk["metadata"]["page"] == 4 for chunk in chunks)


def test_chunk_pages_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_pages([], chunk_size=100, overlap=100)


def test_chunk_pages_skips_blank_pages():
    pages = [{
        "paper_id": "p1",
        "filename": "sample.pdf",
        "page": 1,
        "text": "   ",
    }]
    assert chunk_pages(pages) == []
