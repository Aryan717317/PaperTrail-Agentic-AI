"""
app/research/contradiction.py

Detects and classifies potential contradictions and disagreements across academic papers.
Classifications:
- direct_contradiction
- partial_disagreement
- context_dependent
- compatible
- insufficient_evidence
"""

import json
import logging

from app.llm.openrouter_client import get_llm
from app.schemas import ContradictionAnalysisResponse, ContradictionItem
from app.vectorstore.chroma_store import search_chunks

logger = logging.getLogger(__name__)


def analyze_contradictions(
    topic: str,
    paper_ids: list[str] | None = None,
) -> ContradictionAnalysisResponse:
    """
    Search for passages discussing the given topic and determine if any reported findings conflict.
    """
    docs = search_chunks(topic, k=8, paper_ids=paper_ids)
    if not docs:
        return ContradictionAnalysisResponse(
            topic=topic,
            findings=[],
            overall_assessment="No relevant passages were found on this topic across the indexed papers.",
        )

    evidence_by_paper: dict[str, list[str]] = {}
    for d in docs:
        meta = d.metadata or {}
        fn = meta.get("filename", "Unknown Paper")
        pg = meta.get("page", 1)
        if fn not in evidence_by_paper:
            evidence_by_paper[fn] = []
        evidence_by_paper[fn].append(f"[p.{pg}] {d.page_content}")

    if len(evidence_by_paper) < 2:
        return ContradictionAnalysisResponse(
            topic=topic,
            findings=[],
            overall_assessment=(
                "At least two distinct papers are required to detect cross-paper contradictions. "
                f"Currently retrieved passages only come from: {', '.join(evidence_by_paper.keys())}."
            ),
        )

    corpus = []
    for fn, passages in evidence_by_paper.items():
        corpus.append(f"=== PAPER: {fn} ===\n" + "\n".join(passages))

    prompt = f"""You are an expert scientific peer reviewer analyzing disagreements between research papers.
Topic of investigation: {topic}

Analyze whether the papers genuinely contradict each other or if differences are explained by differing experimental conditions (e.g. different datasets, metrics, training regimes, or task definitions).

Return ONLY a valid JSON object matching this schema:
{{
  "findings": [
    {{
      "topic": "{topic}",
      "paper_a": "Filename A",
      "claim_a": "Specific claim or result in Paper A",
      "paper_b": "Filename B",
      "claim_b": "Specific claim or result in Paper B",
      "relationship": "direct_contradiction | partial_disagreement | context_dependent | compatible | insufficient_evidence",
      "explanation": "Detailed rationale for this classification.",
      "divergent_factors": ["Factors that explain or cause the discrepancy"]
    }}
  ],
  "overall_assessment": "Summary synthesis of academic consensus or divergence on this topic."
}}

Excerpts:
{chr(10).join(corpus)}
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
        items = [
            ContradictionItem(
                topic=item.get("topic", topic),
                paper_a=item.get("paper_a", "Paper A"),
                claim_a=item.get("claim_a", ""),
                paper_b=item.get("paper_b", "Paper B"),
                claim_b=item.get("claim_b", ""),
                relationship=item.get("relationship", "context_dependent"),
                explanation=item.get("explanation", ""),
                divergent_factors=item.get("divergent_factors", []),
            )
            for item in data.get("findings", [])
        ]
        return ContradictionAnalysisResponse(
            topic=topic,
            findings=items,
            overall_assessment=data.get("overall_assessment", ""),
        )
    except Exception as exc:
        logger.error("Error analyzing contradictions: %s", exc)
        return ContradictionAnalysisResponse(
            topic=topic,
            findings=[],
            overall_assessment=f"Contradiction analysis failed: {str(exc)}",
        )
