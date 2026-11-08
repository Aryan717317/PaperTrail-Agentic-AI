"""
app/schemas.py

Pydantic schemas for requests and responses across PaperTrail API endpoints.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Basic Q&A / RAG Schemas
# ============================================================================

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    paper_ids: list[str] | None = None


class Source(BaseModel):
    source_id: str
    paper_id: str
    filename: str
    page: int
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    limitations: list[str]


# ============================================================================
# Document Management Schemas
# ============================================================================

class DocumentInfo(BaseModel):
    paper_id: str
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    total_documents: int
    documents: list[DocumentInfo]


class UploadResponse(BaseModel):
    paper_id: str
    filename: str
    pages_extracted: int
    chunks_indexed: int
    status: str


# ============================================================================
# Research Intelligence Schemas
# ============================================================================

class ResearchClaim(BaseModel):
    claim_id: str
    paper_id: str
    filename: str
    page_number: int
    claim: str
    claim_type: Literal[
        "hypothesis",
        "experimental_finding",
        "methodological_claim",
        "performance_claim",
        "limitation",
        "future_work",
    ]
    methodology: str | None = None
    metric: str | None = None
    evidence_quote: str


class ExtractClaimsRequest(BaseModel):
    paper_id: str | None = None
    topic: str | None = None


class ExtractClaimsResponse(BaseModel):
    claims: list[ResearchClaim]
    summary: str


class PaperComparisonRow(BaseModel):
    attribute: str
    details_by_paper: dict[str, str]  # filename or paper_id -> summary string
    analysis: str


class ComparePapersRequest(BaseModel):
    paper_ids: list[str] = Field(min_length=2, max_length=10)
    focus_topic: str | None = None


class ComparePapersResponse(BaseModel):
    comparison_table: list[PaperComparisonRow]
    synthesis: str
    differing_conditions: list[str]


class ContradictionItem(BaseModel):
    topic: str
    paper_a: str
    claim_a: str
    paper_b: str
    claim_b: str
    relationship: Literal[
        "direct_contradiction",
        "partial_disagreement",
        "context_dependent",
        "compatible",
        "insufficient_evidence",
    ]
    explanation: str
    divergent_factors: list[str]


class ContradictionAnalysisRequest(BaseModel):
    paper_ids: list[str] | None = None
    topic: str


class ContradictionAnalysisResponse(BaseModel):
    topic: str
    findings: list[ContradictionItem]
    overall_assessment: str


class EvidenceAssessmentRequest(BaseModel):
    claim: str
    paper_id: str | None = None


class EvidenceAssessmentResponse(BaseModel):
    claim: str
    directness_of_support: Literal["direct", "indirect", "extrapolated", "unsupported"]
    supporting_excerpts: list[Source]
    caveats_and_limitations: list[str]
    assessment_notes: str
