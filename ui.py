"""
ui.py

Streamlit frontend for PaperTrail: AI-Powered Research Intelligence & Evidence Verification Platform.
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("PAPERTRAIL_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="PaperTrail — Research Intelligence",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 PaperTrail")
st.caption("Evidence-Grounded Research Intelligence & Verification Platform")


def fetch_indexed_papers():
    try:
        res = requests.get(f"{API_URL}/papers", timeout=10)
        if res.ok:
            return res.json().get("documents", [])
    except Exception:
        pass
    return []


# ============================================================================
# Sidebar: Paper Upload & Management
# ============================================================================

with st.sidebar:
    st.header("📚 Document Library")

    uploads = st.file_uploader(
        "Upload research PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if st.button("Index Papers", disabled=not uploads, use_container_width=True):
        for uploaded in uploads:
            with st.spinner(f"Indexing {uploaded.name}..."):
                try:
                    response = requests.post(
                        f"{API_URL}/papers/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                        timeout=180,
                    )
                    if response.ok:
                        data = response.json()
                        st.success(
                            f"✅ {data['filename']}: {data['pages_extracted']} pages, "
                            f"{data['chunks_indexed']} chunks indexed."
                        )
                    else:
                        st.error(f"Error ({uploaded.name}): {response.text}")
                except requests.RequestException as exc:
                    st.error(f"Could not reach API: {exc}")

    st.divider()
    st.subheader("Indexed Papers")
    papers = fetch_indexed_papers()

    selected_paper_ids = []
    if papers:
        for p in papers:
            col1, col2 = st.columns([4, 1])
            with col1:
                chk = st.checkbox(
                    f"{p['filename']} ({p['chunk_count']} chunks)",
                    value=True,
                    key=f"chk_{p['paper_id']}",
                )
                if chk:
                    selected_paper_ids.append(p["paper_id"])
            with col2:
                if st.button("🗑️", key=f"del_{p['paper_id']}", help="Delete paper"):
                    try:
                        requests.delete(f"{API_URL}/papers/{p['paper_id']}", timeout=10)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
    else:
        st.info("No papers indexed yet. Upload PDFs above to begin.")

    st.caption(f"Active scope: {len(selected_paper_ids)} paper(s) selected.")

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
    st.subheader("Ask Your Research Papers")
    st.caption("Ask complex questions across indexed papers. Every substantive claim is cited with source excerpts.")

    question = st.text_area(
        "Research question",
        placeholder="What methodology achieves better retrieval accuracy according to these papers, and what are the limitations?",
        height=100,
    )

    if st.button("Investigate Question", type="primary", disabled=len(question.strip()) < 3):
        with st.spinner("Retrieving evidence and formulating answer..."):
            try:
                payload = {
                    "question": question,
                    "paper_ids": selected_paper_ids if selected_paper_ids else None,
                }
                response = requests.post(f"{API_URL}/questions/ask", json=payload, timeout=180)
            except requests.RequestException as exc:
                st.error(f"Could not reach PaperTrail API: {exc}")
            else:
                if response.ok:
                    result = response.json()
                    st.markdown("### Answer")
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
                            st.write(source["excerpt"])
                            st.caption(f"Paper ID: {source['paper_id']}")
                else:
                    st.error(f"API Error: {response.text}")

# ----------------------------------------------------------------------------
# Tab 2: Claim Extraction
# ----------------------------------------------------------------------------
with tab_claims:
    st.subheader("Structured Research Claim Extraction")
    st.caption("Extract verifiable claims (hypotheses, findings, methodologies, metrics, limitations) directly from papers.")

    topic_focus = st.text_input(
        "Optional topic focus",
        placeholder="e.g. retrieval accuracy, hallucination detection, computational efficiency",
    )
    target_paper = st.selectbox(
        "Select paper to extract from",
        options=["All selected papers"] + [f"{p['filename']} ({p['paper_id']})" for p in papers],
    )

    if st.button("Extract Claims", type="primary"):
        with st.spinner("Analyzing papers and extracting claims..."):
            pid = None
            if target_paper != "All selected papers":
                pid = target_paper.split("(")[-1].strip(")")
            payload = {
                "paper_id": pid,
                "topic": topic_focus.strip() or None,
            }
            try:
                res = requests.post(f"{API_URL}/research/claims", json=payload, timeout=180)
                if res.ok:
                    data = res.json()
                    st.markdown(f"**Summary:** {data.get('summary', '')}")
                    claims = data.get("claims", [])
                    if claims:
                        for c in claims:
                            with st.container():
                                st.markdown(f"#### 🏷️ [{c['claim_type'].replace('_', ' ').title()}] {c['claim']}")
                                colA, colB, colC = st.columns(3)
                                colA.write(f"**Methodology:** {c['methodology'] or 'N/A'}")
                                colB.write(f"**Metric / Result:** {c['metric'] or 'N/A'}")
                                colC.write(f"**Source:** {c['filename']} (p.{c['page_number']})")
                                st.info(f"💬 *Evidence Quote:* \"{c['evidence_quote']}\"")
                                st.divider()
                    else:
                        st.info("No structured claims extracted for this query.")
                else:
                    st.error(res.text)
            except Exception as e:
                st.error(f"Request failed: {e}")

# ----------------------------------------------------------------------------
# Tab 3: Cross-Paper Comparison
# ----------------------------------------------------------------------------
with tab_compare:
    st.subheader("Cross-Paper Comparative Analysis")
    st.caption("Compare multiple papers across methodology, benchmark datasets, metrics, and experimental limitations.")

    if len(selected_paper_ids) < 2:
        st.warning("Please select at least 2 papers from the sidebar to enable cross-paper comparison.")
    else:
        focus = st.text_input("Comparison focus (optional)", placeholder="e.g. retrieval speed vs precision")
        if st.button("Generate Comparison", type="primary"):
            with st.spinner("Comparing selected papers..."):
                try:
                    payload = {
                        "paper_ids": selected_paper_ids,
                        "focus_topic": focus.strip() or None,
                    }
                    res = requests.post(f"{API_URL}/research/compare", json=payload, timeout=180)
                    if res.ok:
                        comp = res.json()
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
                    else:
                        st.error(res.text)
                except Exception as e:
                    st.error(f"Error during comparison: {e}")

# ----------------------------------------------------------------------------
# Tab 4: Contradiction Detection
# ----------------------------------------------------------------------------
with tab_contradictions:
    st.subheader("Disagreement & Contradiction Detection")
    st.caption("Identify conflicting findings, differing conclusions, or context-dependent results between papers.")

    contra_topic = st.text_input(
        "Topic or finding to evaluate",
        placeholder="e.g. Does increasing chunk overlap improve retrieval recall?",
    )
    if st.button("Detect Contradictions", type="primary", disabled=len(contra_topic.strip()) < 3):
        with st.spinner("Analyzing cross-paper divergence..."):
            try:
                payload = {
                    "topic": contra_topic,
                    "paper_ids": selected_paper_ids if selected_paper_ids else None,
                }
                res = requests.post(f"{API_URL}/research/contradictions", json=payload, timeout=180)
                if res.ok:
                    data = res.json()
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
                else:
                    st.error(res.text)
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
        height=80,
    )
    if st.button("Evaluate Evidence Quality", type="primary", disabled=len(test_claim.strip()) < 5):
        with st.spinner("Evaluating evidence directness..."):
            try:
                payload = {
                    "claim": test_claim,
                    "paper_id": selected_paper_ids[0] if len(selected_paper_ids) == 1 else None,
                }
                res = requests.post(f"{API_URL}/research/evidence", json=payload, timeout=180)
                if res.ok:
                    ev = res.json()
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
                else:
                    st.error(res.text)
            except Exception as e:
                st.error(f"Error checking evidence: {e}")

st.divider()
st.caption(
    "PaperTrail MVP 0.2.0 | Evidence-Grounded Research Intelligence | All answers trace to indexed source pages."
)
