import logging
import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.graph import papertrail_graph
from app.ingestion import chunk_pages, extract_pages
from app.schemas import AskRequest, AskResponse, Source
from app.store import add_chunks

logger = logging.getLogger(__name__)
MAX_PDF_BYTES = 25 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024

app = FastAPI(
    title="PaperTrail",
    description="Evidence-grounded research paper assistant MVP",
    version="0.1.1",
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "papertrail"}


@app.post("/papers/upload")
async def upload_paper(file: UploadFile = File(...)):
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a PDF file.")

    temp_path = None
    total_bytes = 0
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            while True:
                chunk = await file.read(UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_PDF_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Maximum PDF size is 25 MB.",
                    )
                tmp.write(chunk)

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        paper_id, pages = extract_pages(temp_path, filename)
        chunks = chunk_pages(pages)
        await run_in_threadpool(add_chunks, chunks)

        return {
            "paper_id": paper_id,
            "filename": filename,
            "pages_extracted": len(pages),
            "chunks_indexed": len(chunks),
            "status": "indexed",
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception("Paper upload/indexing failed for %s", filename)
        raise HTTPException(
            status_code=500,
            detail="The PDF could not be processed or indexed. Check server logs.",
        )
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/questions/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    try:
        result = papertrail_graph.invoke({
            "question": request.question,
            "paper_ids": request.paper_ids,
            "documents": [],
            "answer": "",
            "limitations": [],
            "valid_source_ids": [],
        })
    except Exception:
        logger.exception("Question processing failed")
        raise HTTPException(
            status_code=502,
            detail="Question processing failed. Check server logs and API configuration.",
        )

    sources = []
    for index, doc in enumerate(result.get("documents", []), start=1):
        meta = doc.metadata
        sources.append(Source(
            source_id=f"S{index}",
            paper_id=meta.get("paper_id", ""),
            filename=meta.get("filename", "Unknown paper"),
            page=int(meta.get("page", 0)),
            excerpt=doc.page_content[:500],
        ))

    return AskResponse(
        answer=result.get("answer", ""),
        sources=sources,
        limitations=result.get("limitations", []),
    )
