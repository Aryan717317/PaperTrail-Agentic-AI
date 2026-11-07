"""
app/graph/nodes.py

Deterministic and LLM processing nodes for the PaperTrail research workflow.
"""

import re
import logging
from typing import Any

from app.graph.state import PaperTrailState
from app.llm.openrouter_client import get_llm
from app.vectorstore.chroma_store import search_chunks

logger = logging.getLogger(__name__)


def retrieve_node(state: PaperTrailState) -> dict[str, Any]:
    """Retrieve semantically relevant chunks from persistent vector store."""
    question = state.get("question", "")
    paper_ids = state.get("paper_ids")
    docs = search_chunks(question, k=6, paper_ids=paper_ids)
    return {"documents": docs}


def check_evidence_sufficiency(state: PaperTrailState) -> str:
    """Conditional router: checks if retrieved documents provide sufficient content."""
    docs = state.get("documents", [])
    if not docs:
        return "insufficient"
    total_length = sum(len(d.page_content.strip()) for d in docs)
    if total_length < 50:
        return "insufficient"
    return "sufficient"


def insufficient_evidence_node(state: PaperTrailState) -> dict[str, Any]:
    """Node executed when evidence retrieved is insufficient to answer reliably."""
    return {
        "answer": (
            "I could not retrieve sufficient relevant evidence from the uploaded research papers "
            "to answer this question reliably. Please consider uploading the relevant paper or rephrasing."
        ),
        "valid_source_ids": [],
        "limitations": ["Insufficient or no matching evidence retrieved from indexed documents."],
        "evidence_sufficient": False,
    }


def answer_node(state: PaperTrailState) -> dict[str, Any]:
    """Generate an evidence-grounded answer citing retrieved sources."""
    docs = state.get("documents", [])
    evidence_blocks: list[str] = []
    valid_ids: list[str] = []

    for index, doc in enumerate(docs, start=1):
        source_id = f"S{index}"
        valid_ids.append(source_id)
        meta = doc.metadata or {}
        filename = meta.get("filename", "Unknown paper")
        page = meta.get("page", "unknown")
        evidence_blocks.append(
            f"[{source_id}] {filename}, page {page}\n{doc.page_content}"
        )

    llm = get_llm()
    prompt = f"""You are PaperTrail, an evidence-grounded academic research intelligence assistant.
Answer the user's question using ONLY the provided research excerpts.

Strict Guidelines:
1. Every factual statement must cite its supporting source label (e.g. [S1], [S2]).
2. Do not fabricate results, methodologies, numbers, or claims.
3. Distinguish between an author's stated claims and actual experimental findings.
4. If the provided excerpts do not directly address the question or parts of it, state clearly what is missing.
5. If there are contradictions or differing experimental setups across papers, point them out explicitly.

Question:
{state.get('question', '')}

Retrieved Research Excerpts:
{chr(10).join(evidence_blocks)}
"""
    try:
        response = llm.invoke(prompt)
        content = response.content
        if not isinstance(content, str):
            content = str(content)
    except Exception as exc:
        logger.error("Error invoking LLM in answer_node: %s", exc)
        raise

    return {
        "answer": content,
        "valid_source_ids": valid_ids,
        "evidence_blocks": evidence_blocks,
        "evidence_sufficient": True,
        "limitations": [],
    }


def citation_check_node(state: PaperTrailState) -> dict[str, Any]:
    """Verify that cited source labels in the draft answer correspond to actual retrieved sources."""
    answer = state.get("answer", "")
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    valid = set(state.get("valid_source_ids", []))
    unknown = sorted(cited - valid)
    limitations = list(state.get("limitations", []))

    if unknown:
        limitations.append(
            f"The answer referenced unverified source labels: {', '.join(unknown)}"
        )

    if answer and not cited and state.get("documents"):
        limitations.append(
            "No specific source labels were identified in the answer. Verify the excerpts manually."
        )

    return {"limitations": limitations}
