"""
ui.py

Streamlit frontend for PaperTrail: AI-Powered Research Intelligence & Evidence Verification Platform.
Dual-Mode Engine:
  1. Connected Mode: Connects to a running FastAPI backend (PAPERTRAIL_API_URL).
  2. Standalone / Cloud Mode: Auto-falls back to direct in-process Python execution
     if the FastAPI server is not running (e.g. Streamlit Community Cloud or single-command local run).
"""

import os
import tempfile
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("PAPERTRAIL_API_URL", "http://127.0.0.1:8000")

# ============================================================================
# Page Configuration & Advanced Theme Injection
# ============================================================================

st.set_page_config(
    page_title="PaperTrail — Research Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Cyber-Academic UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Typography & Colors */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #06090e;
        color: #f1f5f9;
    }

    /* Ambient Glow Background */
    .stApp {
        background-image: 
            radial-gradient(ellipse 70% 40% at 50% -15%, rgba(56, 189, 248, 0.12), transparent 70%),
            radial-gradient(ellipse 50% 30% at 85% 45%, rgba(99, 102, 241, 0.08), transparent 60%);
        background-attachment: fixed;
    }

    /* Header & Hero Brand */
    .hero-container {
        padding: 0.8rem 0 1.6rem 0;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid rgba(56, 189, 248, 0.12);
    }

    .brand-title-wrap {
        display: flex;
        align-items: center;
        gap: 0.9rem;
        margin-bottom: 0.4rem;
    }

    .brand-icon-box {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #38bdf8 0%, #6366f1 50%, #a855f7 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 18px rgba(56, 189, 248, 0.35);
    }

    .brand-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 40%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .brand-version {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        padding: 0.2rem 0.6rem;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.3);
        color: #38bdf8;
        border-radius: 9999px;
        font-weight: 700;
    }

    .brand-tagline {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-left: 54px;
        font-weight: 400;
    }

    /* Quick Metrics Bar */
    .metrics-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0 1.8rem 0;
    }

    .stat-tile {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(56, 189, 248, 0.14);
        border-radius: 14px;
        padding: 0.9rem 1.2rem;
        backdrop-filter: blur(12px);
        transition: transform 0.2s, border-color 0.2s;
    }

    .stat-tile:hover {
        border-color: rgba(56, 189, 248, 0.35);
        transform: translateY(-2px);
    }

    .stat-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #fff;
        letter-spacing: -0.02em;
    }

    .stat-val span {
        color: #38bdf8;
    }

    .stat-lbl {
        color: #64748b;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.6rem;
        background: rgba(11, 17, 30, 0.8);
        padding: 0.45rem;
        border-radius: 14px;
        border: 1px solid rgba(56, 189, 248, 0.12);
        margin-bottom: 1.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.6rem 1.3rem;
        font-weight: 600;
        font-size: 0.95rem;
        color: #94a3b8;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #f1f5f9;
        background: rgba(30, 41, 59, 0.5);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.18) 0%, rgba(99, 102, 241, 0.15) 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.15);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
        color: #ffffff;
        font-weight: 700;
        font-size: 0.95rem;
        padding: 0.65rem 1.6rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 4px 16px rgba(14, 165, 233, 0.25);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 22px rgba(14, 165, 233, 0.4);
        border-color: rgba(56, 189, 248, 0.5);
        color: #fff;
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Inputs & Text Areas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: rgba(11, 18, 32, 0.85) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        font-size: 0.98rem !important;
        padding: 0.8rem 1rem !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25) !important;
    }

    /* Card Panels */
    .result-card {
        background: rgba(14, 22, 38, 0.75);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        padding: 1.6rem;
        margin: 1.2rem 0;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(14px);
    }

    .result-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #38bdf8;
        margin-bottom: 0.9rem;
    }

    .citation-bubble {
        display: inline-block;
        background: rgba(56, 189, 248, 0.16);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 0.1rem 0.5rem;
        border-radius: 6px;
        margin: 0 0.2rem;
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(56, 189, 248, 0.12) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }

    /* Sidebar Customizations */
    [data-testid="stSidebar"] {
        background-color: #080d16;
        border-right: 1px solid rgba(56, 189, 248, 0.1);
    }

    .sidebar-section-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #38bdf8;
        margin: 1.2rem 0 0.6rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Dual-Mode Backend Adapters (FastAPI vs In-Process)
# ============================================================================

@st.cache_data(ttl=5)
def is_api_alive() -> bool:
    """Check if the FastAPI backend server is reachable."""
    try:
        res = requests.get(f"{API_URL}/health", timeout=1.5)
        return res.status_code == 200
    except Exception:
        return False


def backend_list_papers() -> list[dict]:
    if is_api_alive():
        try:
            r = requests.get(f"{API_URL}/papers", timeout=10)
            if r.ok:
                return r.json().get("documents", [])
        except Exception:
            pass
    # In-process fallback
    from app.services.document_service import get_all_documents
    doc_resp = get_all_documents()
    return [d.model_dump() for d in doc_resp.documents]


def backend_upload_paper(filename: str, file_bytes: bytes) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/papers/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.services.document_service import process_and_index_pdf
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            temp_path = tmp.name
            tmp.write(file_bytes)
        resp = process_and_index_pdf(temp_path, filename)
        return resp.model_dump()
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def backend_delete_paper(paper_id: str) -> dict:
    if is_api_alive():
        r = requests.delete(f"{API_URL}/papers/{paper_id}", timeout=10)
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.services.document_service import remove_document
    removed = remove_document(paper_id)
    return {"status": "deleted", "paper_id": paper_id, "chunks_removed": removed}


def backend_ask_question(question: str, paper_ids: list[str] | None) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/questions/ask",
            json={"question": question, "paper_ids": paper_ids},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.graph.workflow import papertrail_graph
    result = papertrail_graph.invoke({
        "question": question,
        "paper_ids": paper_ids,
        "documents": [],
        "answer": "",
        "limitations": [],
        "valid_source_ids": [],
    })
    sources = []
    for index, doc in enumerate(result.get("documents", []), start=1):
        meta = doc.metadata or {}
        sources.append({
            "source_id": f"S{index}",
            "paper_id": meta.get("paper_id", ""),
            "filename": meta.get("filename", "Unknown paper"),
            "page": int(meta.get("page", 0)),
            "excerpt": doc.page_content[:500],
        })
    return {
        "answer": result.get("answer", ""),
        "sources": sources,
        "limitations": result.get("limitations", []),
    }


def backend_extract_claims(paper_id: str | None, topic: str | None) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/research/claims",
            json={"paper_id": paper_id, "topic": topic},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.research.claim_extractor import extract_claims
    claims, summary = extract_claims(paper_id=paper_id, topic=topic)
    return {
        "claims": [c.model_dump() for c in claims],
        "summary": summary,
    }


def backend_compare_papers(paper_ids: list[str], focus_topic: str | None) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/research/compare",
            json={"paper_ids": paper_ids, "focus_topic": focus_topic},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.research.comparison import compare_papers
    comp = compare_papers(paper_ids=paper_ids, focus_topic=focus_topic)
    return comp.model_dump()


def backend_check_contradictions(topic: str, paper_ids: list[str] | None) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/research/contradictions",
            json={"topic": topic, "paper_ids": paper_ids},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.research.contradiction import analyze_contradictions
    res = analyze_contradictions(topic=topic, paper_ids=paper_ids)
    return res.model_dump()


def backend_evaluate_evidence(claim: str, paper_id: str | None) -> dict:
    if is_api_alive():
        r = requests.post(
            f"{API_URL}/research/evidence",
            json={"claim": claim, "paper_id": paper_id},
            timeout=180,
        )
        if r.ok:
            return r.json()
        raise RuntimeError(r.text)

    # In-process fallback
    from app.research.evidence import assess_evidence_for_claim
    res = assess_evidence_for_claim(claim=claim, paper_id=paper_id)
    return res.model_dump()


# ============================================================================
# Sidebar: Paper Upload & Management
# ============================================================================

with st.sidebar:
    st.markdown("### 📚 Literature Library")

    # Engine Status Badge
    if is_api_alive():
        st.markdown(
            f'<div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); color:#34d399; '
            f'padding:0.35rem 0.75rem; border-radius:8px; font-size:0.8rem; font-weight:700; margin-bottom:1rem;">'
            f'🟢 CONNECTED: FastAPI Server</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.3); color:#38bdf8; '
            'padding:0.35rem 0.75rem; border-radius:8px; font-size:0.8rem; font-weight:700; margin-bottom:1rem;">'
            '⚡ IN-PROCESS: Standalone Engine</div>',
            unsafe_allow_html=True,
        )

    uploads = st.file_uploader(
        "Upload research PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload academic papers. Scanned image-only PDFs require selectable text.",
    )
    if st.button("📥 Index Uploaded PDFs", disabled=not uploads, use_container_width=True, type="primary"):
        for uploaded in uploads:
            with st.spinner(f"Processing & indexing {uploaded.name}..."):
                try:
                    data = backend_upload_paper(uploaded.name, uploaded.getvalue())
                    st.success(
                        f"✅ **{data['filename']}**\n\n"
                        f"- Pages extracted: {data['pages_extracted']}\n"
                        f"- Chunks indexed: {data['chunks_indexed']}"
                    )
                except Exception as exc:
                    st.error(f"Error ({uploaded.name}): {exc}")

    st.markdown('<div class="sidebar-section-title">Indexed Documents</div>', unsafe_allow_html=True)
    papers = backend_list_papers()

    selected_paper_ids = []
    if papers:
        for p in papers:
            col1, col2 = st.columns([5, 1])
            with col1:
                chk = st.checkbox(
                    f"{p['filename']}",
                    value=True,
                    key=f"chk_{p['paper_id']}",
                    help=f"{p['chunk_count']} embedded vectors in ChromaDB",
                )
                if chk:
                    selected_paper_ids.append(p["paper_id"])
            with col2:
                if st.button("✕", key=f"del_{p['paper_id']}", help="Delete paper"):
                    try:
                        backend_delete_paper(p["paper_id"])
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.info("No documents indexed. Upload papers above to begin research exploration.")

    st.markdown(f"<span style='color:#64748b; font-size:0.8rem;'>Active scope: <strong style='color:#38bdf8;'>{len(selected_paper_ids)}</strong> of {len(papers)} papers</span>", unsafe_allow_html=True)


# ============================================================================
# Main Header & Metric Ribbon
# ============================================================================

total_chunks_count = sum(p.get("chunk_count", 0) for p in papers)

st.markdown(f"""
<div class="hero-container">
    <div class="brand-title-wrap">
        <div class="brand-icon-box">🔬</div>
        <h1 class="brand-title">PaperTrail</h1>
        <span class="brand-version">v0.2.0</span>
    </div>
    <div class="brand-tagline">AI-Powered Research Intelligence & Evidence Verification Platform</div>
</div>

<div class="metrics-bar">
    <div class="stat-tile">
        <div class="stat-lbl">Active Scope</div>
        <div class="stat-val">{len(selected_paper_ids)} <span>Papers</span></div>
    </div>
    <div class="stat-tile">
        <div class="stat-lbl">Vector Index</div>
        <div class="stat-val">{total_chunks_count} <span>Chunks</span></div>
    </div>
    <div class="stat-tile">
        <div class="stat-lbl">Dense Embedding</div>
        <div class="stat-val">384<span>D CPU</span></div>
    </div>
    <div class="stat-tile">
        <div class="stat-lbl">Orchestration</div>
        <div class="stat-val">Lang<span>Graph</span></div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# Research Intelligence Workspace Tabs
# ============================================================================

tab_qa, tab_claims, tab_compare, tab_contradictions, tab_evidence = st.tabs([
    "💬 Evidence-Grounded Q&A",
    "📑 Claim Extraction",
    "⚖️ Cross-Paper Comparison",
    "⚡ Contradiction Detection",
    "🔍 Evidence Quality Check",
])

# ----------------------------------------------------------------------------
# Tab 1: Evidence-Grounded Q&A
# ----------------------------------------------------------------------------
with tab_qa:
    st.markdown("#### Interrogate Indexed Research Papers")
    st.caption("Ask questions across all indexed papers. Every statement is grounded with traceable source page references.")

    # Quick prompt chips
    st.markdown("<span style='font-size:0.82rem; font-weight:700; color:#64748b;'>QUICK RESEARCH PROMPTS:</span>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        if st.button("📊 Main Experimental Findings", use_container_width=True):
            st.session_state["query_input"] = "What are the primary experimental findings and performance metrics reported across these papers?"
    with c_p2:
        if st.button("⚠️ Reported Research Limitations", use_container_width=True):
            st.session_state["query_input"] = "What explicit limitations, caveats, or dataset constraints do the authors report?"
    with c_p3:
        if st.button("⚖️ Compare Retrieval Methodologies", use_container_width=True):
            st.session_state["query_input"] = "How do the proposed methodologies compare in terms of computational complexity and retrieval recall?"

    query_default = st.session_state.get("query_input", "")
    question = st.text_area(
        "Research Query",
        value=query_default,
        placeholder="e.g. What evidence is provided regarding recall improvements, and under what experimental setups?",
        height=110,
        label_visibility="collapsed",
    )

    col_btn, _ = st.columns([2, 5])
    with col_btn:
        run_qa = st.button("🔍 Investigate Literature", type="primary", disabled=len(question.strip()) < 3, use_container_width=True)

    if run_qa:
        with st.spinner("Retrieving semantic vectors & synthesizing grounded answer..."):
            try:
                pids = selected_paper_ids if selected_paper_ids else None
                result = backend_ask_question(question, pids)

                st.markdown("""
                <div class="result-card">
                    <div class="result-header">
                        <span>📝 Grounded Synthesis</span>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(result["answer"])
                st.markdown("</div>", unsafe_allow_html=True)

                if result.get("limitations"):
                    st.warning("⚠️ **Observed Limitations & Evidence Disclaimers:**\n\n- " + "\n- ".join(result["limitations"]))

                st.markdown("#### 📖 Retrieved Source Provenance")
                sources = result.get("sources", [])
                if not sources:
                    st.info("No supporting passages retrieved.")
                for s in sources:
                    with st.expander(f"[{s['source_id']}] {s['filename']} — Page {s['page']}"):
                        st.markdown(f"> *\"{s['excerpt']}\"*")
                        st.caption(f"Paper UUID: `{s['paper_id']}`")
            except Exception as exc:
                st.error(f"Error during query execution: {exc}")

# ----------------------------------------------------------------------------
# Tab 2: Structured Claim Extraction
# ----------------------------------------------------------------------------
with tab_claims:
    st.markdown("#### Structured Research Claim Mining")
    st.caption("Deconstruct papers into structured scientific claims (findings, hypotheses, metrics, limitations) backed by verbatim quotes.")

    c_topic, c_paper = st.columns([1, 1])
    with c_topic:
        topic_focus = st.text_input(
            "Optional Focus Theme",
            placeholder="e.g. retrieval accuracy, hallucination detection, computational efficiency",
        )
    with c_paper:
        target_paper = st.selectbox(
            "Select Literature Scope",
            options=["All selected papers"] + [f"{p['filename']} ({p['paper_id']})" for p in papers],
        )

    if st.button("📑 Mine Empirical Claims", type="primary"):
        with st.spinner("Extracting verifiable claims from literature excerpts..."):
            pid = None
            if target_paper != "All selected papers":
                pid = target_paper.split("(")[-1].strip(")")
            topic_arg = topic_focus.strip() or None
            try:
                data = backend_extract_claims(pid, topic_arg)
                st.markdown(f"**Executive Synthesis:** {data.get('summary', '')}")
                claims = data.get("claims", [])
                if claims:
                    for c in claims:
                        badge_color = {
                            "experimental_finding": "green",
                            "hypothesis": "blue",
                            "methodological_claim": "violet",
                            "performance_claim": "rainbow",
                            "limitation": "orange",
                            "future_work": "gray",
                        }.get(c["claim_type"], "blue")

                        with st.container():
                            st.markdown(f"#### :{badge_color}[{c['claim_type'].replace('_', ' ').upper()}] — {c['claim']}")
                            cA, cB, cC = st.columns(3)
                            cA.markdown(f"**Methodology:** `{c['methodology'] or 'N/A'}`")
                            cB.markdown(f"**Metric / Result:** `{c['metric'] or 'N/A'}`")
                            cC.markdown(f"**Provenance:** `{c['filename']}` *(p.{c['page_number']})*")
                            st.info(f"💬 *Direct Quote:* \"{c['evidence_quote']}\"")
                            st.divider()
                else:
                    st.info("No structured claims extracted for this query.")
            except Exception as e:
                st.error(f"Claim extraction failed: {e}")

# ----------------------------------------------------------------------------
# Tab 3: Cross-Paper Comparative Analysis
# ----------------------------------------------------------------------------
with tab_compare:
    st.markdown("#### Cross-Paper Comparative Matrix")
    st.caption("Side-by-side evaluation of methodologies, benchmark datasets, evaluation metrics, and reported limitations.")

    if len(selected_paper_ids) < 2:
        st.warning("👉 Please select at least **2 papers** in the sidebar to generate a cross-paper comparison matrix.")
    else:
        focus = st.text_input("Comparison Axis (optional)", placeholder="e.g. latency vs precision trade-offs")
        if st.button("⚖️ Generate Comparative Matrix", type="primary"):
            with st.spinner("Contrasting experimental setups across papers..."):
                try:
                    focus_arg = focus.strip() or None
                    comp = backend_compare_papers(selected_paper_ids, focus_arg)

                    st.markdown("### 📊 Synthesis of Differences")
                    st.write(comp.get("synthesis", ""))

                    st.markdown("### 📋 Dimension-by-Dimension Breakdown")
                    for row in comp.get("comparison_table", []):
                        with st.expander(f"**{row['attribute']}**", expanded=True):
                            st.write(f"**Comparative Analysis:** {row['analysis']}")
                            for p_name, detail in row.get("details_by_paper", {}).items():
                                st.markdown(f"- **{p_name}:** {detail}")

                    if comp.get("differing_conditions"):
                        st.markdown("### ⚠️ Divergent Experimental Conditions")
                        for cond in comp["differing_conditions"]:
                            st.markdown(f"- {cond}")
                except Exception as e:
                    st.error(f"Error during comparison: {e}")

# ----------------------------------------------------------------------------
# Tab 4: Contradiction & Disagreement Detection
# ----------------------------------------------------------------------------
with tab_contradictions:
    st.markdown("#### Disagreement & Contradiction Detection")
    st.caption("Identify conflicting findings, differing conclusions, or context-dependent results across literature.")

    contra_topic = st.text_input(
        "Topic or Empirical Finding to Investigate",
        placeholder="e.g. Does increasing chunk overlap improve retrieval recall?",
    )
    if st.button("⚡ Detect Contradictions", type="primary", disabled=len(contra_topic.strip()) < 3):
        with st.spinner("Analyzing cross-paper divergence..."):
            try:
                pids = selected_paper_ids if selected_paper_ids else None
                data = backend_check_contradictions(contra_topic.strip(), pids)

                st.markdown("### 🔍 Literature Consensus & Divergence")
                st.write(data.get("overall_assessment", ""))

                findings = data.get("findings", [])
                if findings:
                    for f in findings:
                        rel_color = {
                            "direct_contradiction": "red",
                            "partial_disagreement": "orange",
                            "context_dependent": "blue",
                            "compatible": "green",
                            "insufficient_evidence": "gray",
                        }.get(f["relationship"], "blue")

                        st.markdown(f"#### :{rel_color}[{f['relationship'].replace('_', ' ').upper()}]")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**{f['paper_a']}**\n\n> {f['claim_a']}")
                        with c2:
                            st.markdown(f"**{f['paper_b']}**\n\n> {f['claim_b']}")
                        st.write(f"**Root Explanation:** {f['explanation']}")
                        if f.get("divergent_factors"):
                            st.caption("Divergent factors: " + ", ".join(f["divergent_factors"]))
                        st.divider()
                else:
                    st.info("No explicit contradictions or disagreements identified for this query.")
            except Exception as e:
                st.error(f"Error checking contradictions: {e}")

# ----------------------------------------------------------------------------
# Tab 5: Evidence Quality Check
# ----------------------------------------------------------------------------
with tab_evidence:
    st.markdown("#### Evidence Strength & Verification")
    st.caption("Test whether an external hypothesis or claim is directly supported, indirectly inferred, extrapolated, or unsupported by your corpus.")

    test_claim = st.text_area(
        "Claim to verify against indexed literature",
        placeholder="e.g. Chunk size of 500 characters always outperforms 1200 characters on domain-specific benchmarks.",
        height=90,
    )
    if st.button("🔍 Evaluate Claim Support", type="primary", disabled=len(test_claim.strip()) < 5):
        with st.spinner("Evaluating evidence directness..."):
            try:
                pid = selected_paper_ids[0] if len(selected_paper_ids) == 1 else None
                ev = backend_evaluate_evidence(test_claim.strip(), pid)

                badge_style = {
                    "direct": "🟢 **Directly Supported by Literature**",
                    "indirect": "🟡 **Indirect / Inferred Support**",
                    "extrapolated": "🟠 **Extrapolated / Speculative Claim**",
                    "unsupported": "🔴 **Unsupported by Indexed Passages**",
                }.get(ev["directness_of_support"], ev["directness_of_support"])

                st.markdown(f"### Assessment: {badge_style}")
                st.write(ev.get("assessment_notes", ""))

                if ev.get("caveats_and_limitations"):
                    st.warning("⚠️ **Author Caveats & Scope Constraints:**\n- " + "\n- ".join(ev["caveats_and_limitations"]))

                st.markdown("#### Supporting Excerpts Inspected")
                for s in ev.get("supporting_excerpts", []):
                    with st.expander(f"[{s['source_id']}] {s['filename']} (p.{s['page']})"):
                        st.write(s["excerpt"])
            except Exception as e:
                st.error(f"Error checking evidence: {e}")

st.divider()
st.markdown(
    "<div style='text-align:center; color:#64748b; font-size:0.85rem;'>"
    "PaperTrail MVP 0.2.0 • Evidence-Grounded Research Intelligence • Built by <strong style='color:#38bdf8;'>Aryan717317</strong>"
    "</div>",
    unsafe_allow_html=True,
)
