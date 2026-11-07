"""
app/research/claim_extractor.py

Extracts structured research claims from indexed paper passages using OpenRouter LLM.
Claims are categorized into:
- hypothesis
- experimental_finding
- methodological_claim
- performance_claim
- limitation
- future_work
"""

import json
import logging
from typing import Any
from uuid import uuid4

from app.llm.openrouter_client import get_llm
from app.schemas import ResearchClaim
from app.vectorstore.chroma_store import search_chunks

logger = logging.getLogger(__name__)


def extract_claims(
    paper_id: str | None = None,
    topic: str | None = None,
    max_passages: int = 8,
) -> tuple[list[ResearchClaim], str]:
    """
    Retrieve passages and extract structured academic claims.
    """
    query = topic or "main research claims, experimental findings, methodology, results and limitations"
    pids = [paper_id] if paper_id else None
    docs = search_chunks(query, k=max_passages, paper_ids=pids)

    if not docs:
        return [], "No relevant passages found for claim extraction."

    evidence_text = []
    for d in docs:
        meta = d.metadata or {}
        fn = meta.get("filename", "Unknown")
        pg = meta.get("page", 1)
        pid = meta.get("paper_id", "")
        evidence_text.append(f"[File: {fn} | Page: {pg} | PaperID: {pid}]\n{d.page_content}")

    prompt = f"""You are an expert academic research intelligence analyst.
Analyze the following excerpts and extract explicit research claims into valid JSON.

For each claim:
- "claim": concise statement of the claim
- "claim_type": choose strictly one of ["hypothesis", "experimental_finding", "methodological_claim", "performance_claim", "limitation", "future_work"]
- "methodology": method or model used (or null if not stated)
- "metric": evaluation metric and score (or null if not stated)
- "evidence_quote": exact short quote from the text that proves this claim
- "filename": filename from header
- "page_number": integer page number from header
- "paper_id": paper_id from header

Return ONLY a JSON object with this structure (no markdown wrapper, just raw JSON):
{{
  "claims": [
    {{
      "claim": "...",
      "claim_type": "experimental_finding",
      "methodology": "...",
      "metric": "...",
      "evidence_quote": "...",
      "filename": "...",
      "page_number": 1,
      "paper_id": "..."
    }}
  ],
  "summary": "High-level summary of the extracted findings across the excerpts."
}}

Excerpts:
{chr(10).join(evidence_text)}
"""
    llm = get_llm()
    try:
        response = llm.invoke(prompt)
        text = response.content
        if not isinstance(text, str):
            text = str(text)

        # Parse JSON output cleanly
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        data = json.loads(cleaned)
        claims_raw = data.get("claims", [])
        summary = data.get("summary", "")

        parsed_claims: list[ResearchClaim] = []
        for c in claims_raw:
            parsed_claims.append(
                ResearchClaim(
                    claim_id=f"CLM-{uuid4().hex[:8]}",
                    paper_id=c.get("paper_id") or (paper_id or "unknown"),
                    filename=c.get("filename") or "unknown",
                    page_number=int(c.get("page_number", 1)),
                    claim=c.get("claim", ""),
                    claim_type=c.get("claim_type", "experimental_finding"),
                    methodology=c.get("methodology"),
                    metric=c.get("metric"),
                    evidence_quote=c.get("evidence_quote", ""),
                )
            )

        return parsed_claims, summary

    except Exception as exc:
        logger.error("Failed to extract structured claims: %s", exc)
        return [], f"Claim extraction failed: {str(exc)}"
