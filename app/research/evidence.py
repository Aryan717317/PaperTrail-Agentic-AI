"""
app/research/evidence.py

Evidence strength and directness evaluation for research claims.
Evaluates whether a claim is directly supported, indirectly inferred, extrapolated, or unsupported.
"""

import json
import logging

from app.llm.openrouter_client import get_llm
from app.schemas import EvidenceAssessmentResponse, Source
from app.vectorstore.chroma_store import search_chunks

logger = logging.getLogger(__name__)


def assess_evidence_for_claim(
    claim: str,
    paper_id: str | None = None,
) -> EvidenceAssessmentResponse:
    """
    Retrieve candidate supporting excerpts for a claim and evaluate the degree of support.
    """
    pids = [paper_id] if paper_id else None
    docs = search_chunks(claim, k=5, paper_ids=pids)

    sources: list[Source] = []
    for idx, d in enumerate(docs, start=1):
        meta = d.metadata or {}
        sources.append(
            Source(
                source_id=f"S{idx}",
                paper_id=meta.get("paper_id", ""),
                filename=meta.get("filename", "Unknown"),
                page=int(meta.get("page", 1)),
                excerpt=d.page_content[:400],
            )
        )

    if not docs:
        return EvidenceAssessmentResponse(
            claim=claim,
            directness_of_support="unsupported",
            supporting_excerpts=[],
            caveats_and_limitations=["No passages relevant to this claim were found."],
            assessment_notes="Cannot assess claim because no matching literature passages exist in the database.",
        )

    evidence_text = "\n".join(
        f"[{s.source_id}] {s.filename} p.{s.page}:\n{s.excerpt}" for s in sources
    )

    prompt = f"""You are a scientific verification expert evaluating evidence quality.
Claim under evaluation:
"{claim}"

Retrieved Excerpts:
{evidence_text}

Task:
Evaluate whether the excerpts directly support, indirectly support, extrapolate, or fail to support the claim.
Do not invent facts.

Return ONLY a valid JSON object matching:
{{
  "directness_of_support": "direct | indirect | extrapolated | unsupported",
  "caveats_and_limitations": ["Notable caveats, scope restrictions, or assumptions made in the text"],
  "assessment_notes": "Transparent explanation of the assessment."
}}
"""
    llm = get_llm()
    try:
        response = llm.invoke(prompt)
        text = response.content
        if not isinstance(text, str):
            text = str(text)

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        data = json.loads(cleaned)
        return EvidenceAssessmentResponse(
            claim=claim,
            directness_of_support=data.get("directness_of_support", "indirect"),
            supporting_excerpts=sources,
            caveats_and_limitations=data.get("caveats_and_limitations", []),
            assessment_notes=data.get("assessment_notes", ""),
        )
    except Exception as exc:
        logger.error("Evidence assessment failed: %s", exc)
        return EvidenceAssessmentResponse(
            claim=claim,
            directness_of_support="unsupported",
            supporting_excerpts=sources,
            caveats_and_limitations=["Assessment model error"],
            assessment_notes=f"Error evaluating claim: {str(exc)}",
        )
