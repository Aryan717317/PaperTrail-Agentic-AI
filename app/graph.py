"""
app/graph.py

Backward-compatible facade delegating to the modular graph package.
"""

from app.graph.state import PaperTrailState
from app.graph.workflow import build_graph, papertrail_graph

__all__ = ["PaperTrailState", "build_graph", "papertrail_graph"]
