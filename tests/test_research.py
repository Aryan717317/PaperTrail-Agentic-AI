import pytest
from app.schemas import (
    AskRequest,
    ComparePapersResponse,
    ContradictionAnalysisResponse,
    ContradictionItem,
    EvidenceAssessmentResponse,
    ExtractClaimsResponse,
    PaperComparisonRow,
    ResearchClaim,
)


def test_research_claim_model():
    claim = ResearchClaim(
        claim_id="CLM-001",
        paper_id="paper_1",
        filename="paper1.pdf",
        page_number=4,
        claim="Method achieves 92% accuracy",
        claim_type="experimental_finding",
        methodology="Hybrid retrieval",
        metric="Recall@10: 92%",
        evidence_quote="Our hybrid model reaches 92% Recall@10.",
    )
    assert claim.claim_id == "CLM-001"
    assert claim.claim_type == "experimental_finding"


def test_research_claim_invalid_type_rejected():
    with pytest.raises(Exception):
        ResearchClaim(
            claim_id="CLM-002",
            paper_id="p",
            filename="f",
            page_number=1,
            claim="c",
            claim_type="invalid_unrecognized_type",  # should fail Literal validation
            evidence_quote="e",
        )


def test_comparison_models():
    row = PaperComparisonRow(
        attribute="Methodology",
        details_by_paper={"paperA.pdf": "Dense retriever", "paperB.pdf": "Sparse BM25"},
        analysis="Dense retriever models semantic similarity better than sparse.",
    )
    resp = ComparePapersResponse(
        comparison_table=[row],
        synthesis="Both papers address retrieval but from divergent angles.",
        differing_conditions=["Different dataset scales"],
    )
    assert len(resp.comparison_table) == 1
    assert resp.comparison_table[0].attribute == "Methodology"


def test_contradiction_models():
    item = ContradictionItem(
        topic="Recall vs Chunk Size",
        paper_a="paperA.pdf",
        claim_a="Chunk size 500 improves recall",
        paper_b="paperB.pdf",
        claim_b="Chunk size 500 degrades recall",
        relationship="context_dependent",
        explanation="Paper A tested on short QA, while Paper B tested on long-form reports.",
        divergent_factors=["Benchmark document lengths differ"],
    )
    resp = ContradictionAnalysisResponse(
        topic="Recall vs Chunk Size",
        findings=[item],
        overall_assessment="Disagreement is context-dependent based on document domain.",
    )
    assert len(resp.findings) == 1
    assert resp.findings[0].relationship == "context_dependent"


def test_evidence_assessment_models():
    resp = EvidenceAssessmentResponse(
        claim="Method X is superior",
        directness_of_support="direct",
        supporting_excerpts=[],
        caveats_and_limitations=["Tested only on English datasets"],
        assessment_notes="Directly proven in table 2.",
    )
    assert resp.directness_of_support == "direct"

