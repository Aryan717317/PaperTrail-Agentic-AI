import pytest
from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_extractor import extract_pages


def test_extract_pages_from_real_pdf():
    paper_id, pages = extract_pages("tests/fixtures/sample_paper.pdf", "sample_paper.pdf")
    assert paper_id is not None
    assert len(paper_id) > 10
    assert len(pages) == 1
    assert pages[0]["filename"] == "sample_paper.pdf"
    assert pages[0]["page"] == 1
    assert "Hybrid retrieval" in pages[0]["text"]


def test_clean_text_removes_page_numbers_and_extra_spaces():
    raw = "   Introduction to RAG.   \n\n4\n\nPage 4\nOur method achieves 95% accuracy.   "
    cleaned = clean_text(raw)
    assert "4" not in cleaned.splitlines()
    assert "Page 4" not in cleaned.splitlines()
    assert "Our method achieves 95% accuracy." in cleaned


def test_chunk_pages_preserves_metadata_and_generates_chunk_id():
    pages = [{
        "paper_id": "test_pid_123",
        "filename": "sample.pdf",
        "page": 2,
        "text": "Machine learning models require robust evaluation metrics. " * 30,
    }]
    chunks = chunk_pages(pages, chunk_size=500, chunk_overlap=100)
    assert len(chunks) > 1
    for c in chunks:
        assert c["metadata"]["paper_id"] == "test_pid_123"
        assert c["metadata"]["filename"] == "sample.pdf"
        assert c["metadata"]["page"] == 2
        assert "chunk_id" in c["metadata"]
        assert c["metadata"]["chunk_id"].startswith("test_pid-p0002-")


def test_chunk_pages_invalid_parameters():
    with pytest.raises(ValueError):
        chunk_pages([], chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError):
        chunk_pages([], chunk_size=-10, chunk_overlap=0)


def test_chunk_pages_skips_blank_pages():
    pages = [{
        "paper_id": "pid_1",
        "filename": "blank.pdf",
        "page": 1,
        "text": "   \n\t  ",
    }]
    assert chunk_pages(pages) == []
