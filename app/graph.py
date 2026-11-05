import re
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.config import get_settings
from app.store import search_chunks


class PaperTrailState(TypedDict):
    question: str
    paper_ids: list[str] | None
    documents: list
    answer: str
    limitations: list[str]
    valid_source_ids: list[str]


def retrieve_node(state: PaperTrailState) -> dict:
    docs = search_chunks(
        state["question"],
        k=6,
        paper_ids=state.get("paper_ids"),
    )
    return {"documents": docs}


def answer_node(state: PaperTrailState) -> dict:
    docs = state["documents"]
    if not docs:
        return {
            "answer": "I couldn't retrieve relevant passages. Upload a paper or rephrase the question.",
            "valid_source_ids": [],
            "limitations": ["No relevant passages were retrieved."],
        }

    evidence_blocks = []
    valid_ids = []
    for index, doc in enumerate(docs, start=1):
        source_id = f"S{index}"
        valid_ids.append(source_id)
        meta = doc.metadata
        evidence_blocks.append(
            f"[{source_id}] {meta.get('filename', 'Unknown paper')}, "
            f"page {meta.get('page', 'unknown')}\n{doc.page_content}"
        )

    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0,
        max_retries=2,
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "PaperTrail",
        },
    )
    prompt = f"""You are PaperTrail, a careful research assistant.
Answer using ONLY the supplied excerpts.
- Cite each substantive factual statement with source labels such as [S1].
- Do not invent results, methods, numbers, or conclusions.
- Distinguish a paper's authors' claims from evidence shown in the excerpt.
- If evidence is incomplete or conflicting, say so explicitly.
- If the excerpts do not answer the question, abstain rather than guess.

Question:
{state['question']}

Retrieved excerpts:
{chr(10).join(evidence_blocks)}
"""
    response = llm.invoke(prompt)
    content = response.content
    if not isinstance(content, str):
        content = str(content)
    return {
        "answer": content,
        "valid_source_ids": valid_ids,
        "limitations": [],
    }


def citation_check_node(state: PaperTrailState) -> dict:
    answer = state["answer"]
    cited = set(re.findall(r"\[(S\d+)\]", answer))
    valid = set(state.get("valid_source_ids", []))
    unknown = sorted(cited - valid)
    limitations = list(state.get("limitations", []))

    if unknown:
        limitations.append(
            "The draft contained unknown citation labels: " + ", ".join(unknown)
        )
    # This checks citation-label integrity only; it does not prove semantic support.
    if answer and not cited and state.get("documents"):
        limitations.append(
            "No source labels were detected in the answer. Treat it as unverified and inspect the excerpts."
        )
    return {"limitations": limitations}


def build_graph():
    graph = StateGraph(PaperTrailState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft_answer", answer_node)
    graph.add_node("citation_check", citation_check_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "draft_answer")
    graph.add_edge("draft_answer", "citation_check")
    graph.add_edge("citation_check", END)
    return graph.compile()


papertrail_graph = build_graph()
