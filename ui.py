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

st.set_page_config(
    page_title="PaperTrail — Research Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Gradient Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #38bdf8 0%, #6366f1 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }

    .brand-sub {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* Enhanced Card Containers */
    .stCard {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s, border-color 0.2s;
    }

    .stCard:hover {
        border-color: rgba(56, 189, 248, 0.35);
        transform: translateY(-2px);
    }

    /* Citation Tag */
    .citation-tag {
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.35);
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
    }

    /* Tab enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(15, 23, 42, 0.5);
        padding: 0.4rem;
        border-radius: 12px;
        border: 1px solid rgba(56, 189, 248, 0.1);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.1rem;
        font-weight: 600;
    }

    /* Status Badges */
    .badge-status {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header">🔬 PaperTrail</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">AI-Powered Academic Research Intelligence & Evidence Verification Platform</div>', unsafe_allow_html=True)


# ============================================================================
# Dual-Mode Backend Adapters
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
    st.header("📚 Document Library")

    # Mode indicator
    if is_api_alive():
        st.success(f"🟢 **Mode:** FastAPI Server (`{API_URL}`)")
    else:
        st.info("⚡ **Mode:** In-Process Engine (Standalone / Cloud)")

    uploads = st.file_uploader(
        "Upload research PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if st.button("📥 Index Selected Papers", disabled=not uploads, use_container_width=True, type="primary"):
        for uploaded in uploads:
            with st.spinner(f"Indexing {uploaded.name}..."):
                try:
                    data = backend_upload_paper(uploaded.name, uploaded.getvalue())
                    st.success(
                        f"✅ **{data['filename']}**\n\n"
                        f"- {data['pages_extracted']} pages extracted\n"
                        f"- {data['chunks_indexed']} chunks indexed"
                    )
                except Exception as exc:
                    st.error(f"Error ({uploaded.name}): {exc}")

    st.divider()
    st.subheader("Indexed Literature")
    papers = backend_list_papers()

    selected_paper_ids = []
    if papers:
        for p in papers:
            col1, col2 = st.columns([4, 1])
            with col1:
                chk = st.checkbox(
                    f"{p['filename']}",
                    value=True,
                    key=f"chk_{p['paper_id']}",
                    help=f"{p['chunk_count']} embedded chunks",
                )
                if chk:
                    selected_paper_ids.append(p["paper_id"])
            with col2:
                if st.button("🗑️", key=f"del_{p['paper_id']}", help="Delete paper from vector store"):
                    try:
                        backend_delete_paper(p["paper_id"])
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.info("No papers indexed yet. Upload PDFs above to begin your research session.")

    st.caption(f"Active scope: **{len(selected_paper_ids)}** of {len(papers)} paper(s) selected.")


# ============================================================================
# Main Content: Research Intelligence Tabs
# ============================================================================

tab_qa, tab_claims, tab_compare, tab_contradictions, tab_evidence = st.tabs([
    "💬 Evidence-Grounded Q&A",
    "📑 Claim Extraction",
    "⚖️ Cross-Paper Comparison",
    "⚡ Contradiction Detection",
    "🔍 Evidence Quality Check",
])

# ----------------------------------------------------------------------------
# Tab 1: Q&A
# ----------------------------------------------------------------------------
with tab_qa:
    st.subheader("Interrogate Your Research Papers")
    st.caption("Ask questions across all indexed papers. Every substantive statement is anchored with traceable page citations.")

    question = st.text_area(
        "Enter your research query",
        placeholder="e.g. What methodology achieves better retrieval accuracy according to these papers, and what are the limitations?",
        height=110,
    )

    col_btn, _ = st.columns([2, 5])
    with col_btn:
        run_qa = st.button("🔍 Investigate Literature", type="primary", disabled=len(question.strip()) < 3, use_container_width=True)

    if run_qa:
        with st.spinner("Synthesizing evidence across papers..."):
            try:
                pids = selected_paper_ids if selected_paper_ids else None
                result = backend_ask_question(question, pids)

                st.markdown("### 📝 Grounded Synthesis")
                st.write(result["answer"])

                if result.get("limitations"):
                    st.warning("⚠️ **Observed Limitations & Disclaimers:**\n\n- " + "\n- ".join(result["limitations"]))

                st.markdown("### 📖 Retrieved Evidence Excerpts")
                sources = result.get("sources", [])
                if not sources:
                    st.info("No source excerpts retrieved.")
                for source in sources:
                    with st.expander(
                        f"[{source['source_id']}] {source['filename']} — Page {source['page']}"
                    ):
                        st.markdown(f"> *{source['excerpt']}*")
                        st.caption(f"Paper UUID: `{source['paper_id']}`")
            except Exception as exc:
                st.error(f"Error during query: {exc}")

# ----------------------------------------------------------------------------
# Tab 2: Claim Extraction
# ----------------------------------------------------------------------------
with tab_claims:
    st.subheader("Structured Research Claim Extraction")
    st.caption("Extract hypotheses, findings, methodologies, metrics, and limitations into structured scientific claims.")

    c_topic, c_paper = st.columns([1, 1])
    with c_topic:
        topic_focus = st.text_input(
            "Optional topic focus",
            placeholder="e.g. retrieval accuracy, hallucination detection, computational efficiency",
        )
    with c_paper:
        target_paper = st.selectbox(
            "Select paper scope",
            options=["All selected papers"] + [f"{p['filename']} ({p['paper_id']})" for p in papers],
        )

    if st.button("📑 Extract Structured Claims", type="primary"):
        with st.spinner("Mining papers for empirical claims..."):
            pid = None
            if target_paper != "All selected papers":
                pid = target_paper.split("(")[-1].strip(")")
            topic_arg = topic_focus.strip() or None
            try:
                data = backend_extract_claims(pid, topic_arg)
                st.markdown(f"**Synthesis:** {data.get('summary', '')}")
                claims = data.get("claims", [])
                if claims:
                    for c in claims:
                        with st.container():
                            badge_color = {
                                "experimental_finding": "green",
                                "hypothesis": "blue",
                                "methodological_claim": "violet",
                                "performance_claim": "rainbow",
                                "limitation": "orange",
                                "future_work": "gray",
                            }.get(c["claim_type"], "blue")

                            st.markdown(f"#### :{badge_color}[{c['claim_type'].replace('_', ' ').title()}] — {c['claim']}")
                            colA, colB, colC = st.columns(3)
                            colA.markdown(f"**Methodology:** `{c['methodology'] or 'N/A'}`")
                            colB.markdown(f"**Metric / Result:** `{c['metric'] or 'N/A'}`")
                            colC.markdown(f"**Provenance:** `{c['filename']}` *(p.{c['page_number']})*")
                            st.info(f"💬 *Verbatim Evidence Quote:* \"{c['evidence_quote']}\"")
                            st.divider()
                else:
                    st.info("No structured claims extracted for this query.")
            except Exception as e:
                st.error(f"Claim extraction failed: {e}")

# ----------------------------------------------------------------------------
# Tab 3: Cross-Paper Comparison
# ----------------------------------------------------------------------------
with tab_compare:
    st.subheader("Cross-Paper Comparative Analysis")
    st.caption("Compare multiple papers across methodology, benchmark datasets, evaluation metrics, and reported limitations.")

    if len(selected_paper_ids) < 2:
        st.warning("👉 Please select at least **2 papers** in the sidebar to generate a cross-paper comparison matrix.")
    else:
        focus = st.text_input("Comparison focus (optional)", placeholder="e.g. retrieval speed vs precision trade-offs")
        if st.button("⚖️ Generate Comparative Matrix", type="primary"):
            with st.spinner("Contrasting experimental setups and results..."):
                try:
                    focus_arg = focus.strip() or None
                    comp = backend_compare_papers(selected_paper_ids, focus_arg)

                    st.markdown("### 📊 Comparative Synthesis")
                    st.write(comp.get("synthesis", ""))

                    st.markdown("### 📋 Dimension-by-Dimension Breakdown")
                    for row in comp.get("comparison_table", []):
                        with st.expander(f"**{row['attribute']}**", expanded=True):
                            st.write(f"**Analysis:** {row['analysis']}")
                            for p_name, detail in row.get("details_by_paper", {}).items():
                                st.markdown(f"- **{p_name}:** {detail}")

                    if comp.get("differing_conditions"):
                        st.markdown("### ⚠️ Key Differences in Experimental Setup")
                        for cond in comp["differing_conditions"]:
                            st.markdown(f"- {cond}")
                except Exception as e:
                    st.error(f"Error during comparison: {e}")

# ----------------------------------------------------------------------------
# Tab 4: Contradiction Detection
# ----------------------------------------------------------------------------
with tab_contradictions:
    st.subheader("Disagreement & Contradiction Detection")
    st.caption("Identify conflicting findings, differing conclusions, or context-dependent results across your literature corpus.")

    contra_topic = st.text_input(
        "Topic or empirical finding to evaluate",
        placeholder="e.g. Does increasing chunk overlap improve retrieval recall?",
    )
    if st.button("⚡ Detect Contradictions", type="primary", disabled=len(contra_topic.strip()) < 3):
        with st.spinner("Analyzing cross-paper divergence..."):
            try:
                pids = selected_paper_ids if selected_paper_ids else None
                data = backend_check_contradictions(contra_topic.strip(), pids)

                st.markdown("### 🔍 Overall Disagreement Assessment")
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

                        st.markdown(
                            f"#### :{rel_color}[{f['relationship'].replace('_', ' ').upper()}]"
                        )
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**{f['paper_a']}**\n\n> {f['claim_a']}")
                        with c2:
                            st.markdown(f"**{f['paper_b']}**\n\n> {f['claim_b']}")
                        st.write(f"**Explanation:** {f['explanation']}")
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
    st.subheader("Evidence Strength & Directness Check")
    st.caption("Test whether a specific claim is directly supported, indirectly inferred, extrapolated, or unsupported by your paper collection.")

    test_claim = st.text_area(
        "Claim to verify against literature",
        placeholder="e.g. Chunk size of 500 characters always outperforms 1200 characters on domain-specific benchmarks.",
        height=90,
    )
    if st.button("🔍 Evaluate Evidence Quality", type="primary", disabled=len(test_claim.strip()) < 5):
        with st.spinner("Evaluating evidence directness..."):
            try:
                pid = selected_paper_ids[0] if len(selected_paper_ids) == 1 else None
                ev = backend_evaluate_evidence(test_claim.strip(), pid)

                badge_style = {
                    "direct": "🟢 **Directly Supported by Evidence**",
                    "indirect": "🟡 **Indirectly Inferred Support**",
                    "extrapolated": "🟠 **Extrapolated / Speculative Claim**",
                    "unsupported": "🔴 **Unsupported by Available Texts**",
                }.get(ev["directness_of_support"], ev["directness_of_support"])

                st.markdown(f"### Assessment: {badge_style}")
                st.write(ev.get("assessment_notes", ""))

                if ev.get("caveats_and_limitations"):
                    st.warning("⚠️ **Author Caveats / Limitations:**\n- " + "\n- ".join(ev["caveats_and_limitations"]))

                st.markdown("### Supporting Excerpts Inspected")
                for s in ev.get("supporting_excerpts", []):
                    with st.expander(f"[{s['source_id']}] {s['filename']} (p.{s['page']})"):
                        st.write(s["excerpt"])
            except Exception as e:
                st.error(f"Error checking evidence: {e}")

st.divider()
st.caption(
    "PaperTrail MVP 0.2.0 | Dual-Mode Engine | Built by Aryan717317"
)
