"""
app/graph/workflow.py

Constructs and compiles the PaperTrail LangGraph research workflow.
"""

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    answer_node,
    check_evidence_sufficiency,
    citation_check_node,
    insufficient_evidence_node,
    retrieve_node,
)
from app.graph.state import PaperTrailState


def build_graph():
    """
    Build the research graph:
    START -> retrieve -> [evidence_sufficient?]
      - sufficient -> draft_answer -> citation_check -> END
      - insufficient -> report_insufficient -> END
    """
    builder = StateGraph(PaperTrailState)

    builder.add_node("retrieve", retrieve_node)
    builder.add_node("draft_answer", answer_node)
    builder.add_node("citation_check", citation_check_node)
    builder.add_node("report_insufficient", insufficient_evidence_node)

    builder.add_edge(START, "retrieve")
    builder.add_conditional_edges(
        "retrieve",
        check_evidence_sufficiency,
        {
            "sufficient": "draft_answer",
            "insufficient": "report_insufficient",
        },
    )
    builder.add_edge("draft_answer", "citation_check")
    builder.add_edge("citation_check", END)
    builder.add_edge("report_insufficient", END)

    return builder.compile()


papertrail_graph = build_graph()
