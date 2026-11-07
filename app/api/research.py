"""
app/api/research.py

Endpoints for questions Q&A, structured claim extraction, cross-paper comparison,
contradiction detection, and evidence assessment.
"""

import logging
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from app.graph.workflow import papertrail_graph
from app.research.claim_extractor import extract_claims
from app.research.comparison import compare_papers
from app.research.contradiction import analyze_contradictions
from app.research.evidence import assess_evidence_for_claim
from app.schemas import (
    AskRequest,
    AskResponse,
    ComparePapersRequest,
    ComparePapersResponse,
    ContradictionAnalysisRequest,
    ContradictionAnalysisResponse,
    EvidenceAssessmentRequest,
    EvidenceAssessmentResponse,
    ExtractClaimsRequest,
    ExtractClaimsResponse,
    Source,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Research Intelligence"])


@router.post("/questions/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    try:
        result = await run_in_threadpool(
            papertrail_graph.invoke,
            {
                "question": request.question,
                "paper_ids": request.paper_ids,
                "documents": [],
                "answer": "",
                "limitations": [],
                "valid_source_ids": [],
            },
        )
    except Exception:
        logger.exception("Question processing failed")
        raise HTTPException(
            status_code=502,
            detail="Question processing failed. Check server logs and OpenRouter API configuration.",
        )

    sources = []
    for index, doc in enumerate(result.get("documents", []), start=1):
        meta = doc.metadata or {}
        sources.append(
            Source(
                source_id=f"S{index}",
                paper_id=meta.get("paper_id", ""),
                filename=meta.get("filename", "Unknown paper"),
                page=int(meta.get("page", 0)),
                excerpt=doc.page_content[:500],
            )
        )

    return AskResponse(
        answer=result.get("answer", ""),
        sources=sources,
        limitations=result.get("limitations", []),
    )


@router.post("/research/claims", response_model=ExtractClaimsResponse)
async def get_claims(request: ExtractClaimsRequest):
    try:
        claims, summary = await run_in_threadpool(
            extract_claims,
            paper_id=request.paper_id,
            topic=request.topic,
        )
        return ExtractClaimsResponse(claims=claims, summary=summary)
    except Exception as exc:
        logger.exception("Claim extraction failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/research/compare", response_model=ComparePapersResponse)
async def compare_multiple_papers(request: ComparePapersRequest):
    try:
        response = await run_in_threadpool(
            compare_papers,
            paper_ids=request.paper_ids,
            focus_topic=request.focus_topic,
        )
        return response
    except Exception as exc:
        logger.exception("Paper comparison failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/research/contradictions", response_model=ContradictionAnalysisResponse)
async def check_contradictions(request: ContradictionAnalysisRequest):
    try:
        response = await run_in_threadpool(
            analyze_contradictions,
            topic=request.topic,
            paper_ids=request.paper_ids,
        )
        return response
    except Exception as exc:
        logger.exception("Contradiction analysis failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/research/evidence", response_model=EvidenceAssessmentResponse)
async def evaluate_evidence(request: EvidenceAssessmentRequest):
    try:
        response = await run_in_threadpool(
            assess_evidence_for_claim,
            claim=request.claim,
            paper_id=request.paper_id,
        )
        return response
    except Exception as exc:
        logger.exception("Evidence assessment failed")
        raise HTTPException(status_code=500, detail=str(exc))
