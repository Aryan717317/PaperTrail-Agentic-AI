"""
app/research/comparison.py

Structured cross-paper comparison logic.
Compares research papers on methodology, datasets, metrics, findings, and limitations.
"""

import json
import logging
from typing import Any

from app.llm.openrouter_client import get_llm
from app.schemas import ComparePapersResponse, PaperComparisonRow
from app.vectorstore.chroma_store import search_chunks

logger = logging.getLogger(__name__)


def compare_papers(
    paper_ids: list[str],
    focus_topic: str | None = None,
) -> ComparePapersResponse:
    """
    Retrieve evidence from multiple papers and generate a comparative analysis.
    """
    topic_query = focus_topic or "methodology dataset metrics results limitations experimental conditions"
    
    # Retrieve evidence for each paper separately to ensure balanced representation
    passages_by_paper: dict[str, list[str]] = {}
    for pid in paper_ids:
        docs = search_chunks(topic_query, k=4, paper_ids=[pid])
        passages: list[str] = []
        for d in docs:
            fn = (d.metadata or {}).get("filename", pid)
            pg = (d.metadata or {}).get("page", 1)
            passages.append(f"[{fn} p.{pg}]: {d.page_content}")
        passages_by_paper[pid] = passages

    prompt_corpus = []
    for pid, p_list in passages_by_paper.items():
        joined = "\n".join(p_list) if p_list else "No relevant passages found."
        prompt_corpus.append(f"=== PAPER ID: {pid} ===\n{joined}\n")

    prompt = f"""You are an academic researcher conducting a rigorous cross-paper comparative study.
Compare the papers based on the following excerpts. Do not assume metrics or results are directly comparable if datasets or experimental setups differ!

Return ONLY a valid JSON object with the following schema:
{{
  "comparison_table": [
    {{
      "attribute": "Methodology",
      "details_by_paper": {{"paper_1": "...", "paper_2": "..."}},
      "analysis": "Comparative synthesis explaining structural differences."
    }},
    {{
      "attribute": "Datasets & Benchmarks",
      "details_by_paper": {{"paper_1": "...", "paper_2": "..."}},
      "analysis": "..."
    }},
    {{
      "attribute": "Evaluation Metrics & Results",
      "details_by_paper": {{"paper_1": "...", "paper_2": "..."}},
      "analysis": "..."
    }},
    {{
      "attribute": "Reported Limitations",
      "details_by_paper": {{"paper_1": "...", "paper_2": "..."}},
      "analysis": "..."
    }}
  ],
  "synthesis": "Comprehensive comparison highlighting core trade-offs and findings.",
  "differing_conditions": [
    "Differing dataset sizes or domains",
    "Different evaluation baselines",
    "Hardware or training compute differences"
  ]
}}

Excerpts:
{chr(10).join(prompt_corpus)}
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
        rows = [
            PaperComparisonRow(
                attribute=r.get("attribute", "General"),
                details_by_paper=r.get("details_by_paper", {}),
                analysis=r.get("analysis", ""),
            )
            for r in data.get("comparison_table", [])
        ]
        return ComparePapersResponse(
            comparison_table=rows,
            synthesis=data.get("synthesis", "Comparison complete."),
            differing_conditions=data.get("differing_conditions", []),
        )
    except Exception as exc:
        logger.error("Failed to compare papers: %s", exc)
        return ComparePapersResponse(
            comparison_table=[],
            synthesis=f"Comparison failed: {str(exc)}",
            differing_conditions=[],
        )

