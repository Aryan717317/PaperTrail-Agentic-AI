import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


@pytest.fixture
def client(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    test_settings = Settings(
        chroma_path=temp_dir,
        collection_name="test_api_papertrail",
    )
    monkeypatch.setattr("app.vectorstore.chroma_store.get_settings", lambda: test_settings)
    monkeypatch.setattr("app.config.get_settings", lambda: test_settings)

    from app.vectorstore.chroma_store import get_vector_store
    get_vector_store.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    get_vector_store.cache_clear()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "papertrail"}


def test_list_papers_initially_empty(client):
    res = client.get("/papers")
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] == 0
    assert data["documents"] == []


def test_upload_non_pdf_rejected(client):
    res = client.post(
        "/papers/upload",
        files={"file": ("test.txt", b"Hello text", "text/plain")},
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


def test_upload_and_delete_real_pdf(client):
    with open("tests/fixtures/sample_paper.pdf", "rb") as f:
        pdf_bytes = f.read()

    res = client.post(
        "/papers/upload",
        files={"file": ("sample_paper.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "indexed"
    assert data["filename"] == "sample_paper.pdf"
    assert data["pages_extracted"] == 1
    assert data["chunks_indexed"] >= 1
    paper_id = data["paper_id"]

    # Verify listing reflects the uploaded paper
    list_res = client.get("/papers")
    assert list_res.status_code == 200
    papers = list_res.json()["documents"]
    assert any(p["paper_id"] == paper_id for p in papers)

    # Delete the uploaded paper
    del_res = client.delete(f"/papers/{paper_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify document is no longer listed
    list_after = client.get("/papers")
    assert not any(p["paper_id"] == paper_id for p in list_after.json()["documents"])
