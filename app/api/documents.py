"""
app/api/documents.py

Endpoints for document upload, listing, and deletion.
"""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.schemas import DocumentListResponse, UploadResponse
from app.services.document_service import (
    get_all_documents,
    handle_uploaded_file,
    remove_document,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/papers", tags=["Documents"])


@router.post("/upload", response_model=UploadResponse)
async def upload_paper(file: UploadFile = File(...)):
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        response = await handle_uploaded_file(file)
        return response
    except ValueError as exc:
        msg = str(exc)
        if "Maximum PDF size" in msg:
            raise HTTPException(status_code=413, detail=msg)
        raise HTTPException(status_code=422, detail=msg)
    except Exception:
        logger.exception("Upload failed for %s", filename)
        raise HTTPException(
            status_code=500,
            detail="The PDF could not be processed or indexed. Check server logs.",
        )


@router.get("", response_model=DocumentListResponse)
def list_papers():
    return get_all_documents()


@router.delete("/{paper_id}")
def delete_paper(paper_id: str):
    deleted_count = remove_document(paper_id)
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Paper not found or already deleted.")
    return {"status": "deleted", "paper_id": paper_id, "chunks_removed": deleted_count}
