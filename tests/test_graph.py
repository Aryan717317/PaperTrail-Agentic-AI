from langchain_core.documents import Document
from app.graph.nodes import (
    check_evidence_sufficiency,
    citation_check_node,
    insufficient_evidence_node,
)
from app.graph.state import PaperTrailState


def test_evidence_sufficiency_router():
    empty_state: PaperTrailState = {"documents": []}
    assert check_evidence_sufficiency(empty_state) == "insufficient"

    tiny_state: PaperTrailState = {
        "documents": [Document(page_content="short", metadata={})]
    }
    assert check_evidence_sufficiency(tiny_state) == "insufficient"

    sufficient_state: PaperTrailState = {
        "documents": [
            Document(
                page_content="This is a substantive excerpt containing multiple detailed research statements.",
                metadata={},
            )
        ]
    }
    assert check_evidence_sufficiency(sufficient_state) == "sufficient"


def test_insufficient_evidence_node():
    state: PaperTrailState = {"question": "What is the secret?"}
    res = insufficient_evidence_node(state)
    assert res["evidence_sufficient"] is False
    assert "could not retrieve sufficient relevant evidence" in res["answer"]
    assert len(res["limitations"]) > 0


def test_citation_check_node_valid_and_invalid():
    # Case 1: valid citation
    state1: PaperTrailState = {
        "answer": "According to the findings [S1], retrieval improved.",
        "valid_source_ids": ["S1"],
        "documents": [Document(page_content="content")],
        "limitations": [],
    }
    res1 = citation_check_node(state1)
    assert len(res1["limitations"]) == 0

    # Case 2: hallucinated / unknown citation
    state2: PaperTrailState = {
        "answer": "Method achieved 99% accuracy [S5].",
        "valid_source_ids": ["S1"],
        "documents": [Document(page_content="content")],
        "limitations": [],
    }
    res2 = citation_check_node(state2)
    assert any("unverified source labels: S5" in lim for lim in res2["limitations"])

    # Case 3: missing citations when docs exist
    state3: PaperTrailState = {
        "answer": "Method achieved 99% accuracy without citing anything.",
        "valid_source_ids": ["S1"],
        "documents": [Document(page_content="content")],
        "limitations": [],
    }
    res3 = citation_check_node(state3)
    assert any("No specific source labels were identified" in lim for lim in res3["limitations"])
