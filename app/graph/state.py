"""
app/graph/state.py

Defines the typed state representation for the PaperTrail research workflow.
"""

from typing import Any, TypedDict
from langchain_core.documents import Document


class PaperTrailState(TypedDict, total=False):
    question: str
    paper_ids: list[str] | None
    documents: list[Document]
    evidence_blocks: list[str]
    answer: str
    claims: list[dict[str, Any]]
    evidence_sufficient: bool
    limitations: list[str]
    valid_source_ids: list[str]
    warnings: list[str]

