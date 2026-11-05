import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("PAPERTRAIL_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="PaperTrail", page_icon="📄", layout="wide")
st.title("PaperTrail")
st.caption("Ask research questions. Inspect the evidence behind every answer.")

with st.sidebar:
    st.subheader("Add research papers")
    uploads = st.file_uploader(
        "Upload text-based PDF papers",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if st.button("Index selected papers", disabled=not uploads):
        for uploaded in uploads:
            with st.spinner(f"Indexing {uploaded.name}..."):
                try:
                    response = requests.post(
                        f"{API_URL}/papers/upload",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                        timeout=180,
                    )
                except requests.RequestException as exc:
                    st.error(f"Could not reach PaperTrail API: {exc}")
                    continue

            if response.ok:
                data = response.json()
                st.success(
                    f"{data['filename']}: {data['pages_extracted']} pages, "
                    f"{data['chunks_indexed']} chunks indexed."
                )
            else:
                st.error(response.text)

st.subheader("Ask your papers")
question = st.text_area(
    "Research question",
    placeholder="What evidence do these papers provide for their main claims?",
    height=100,
)
if st.button("Investigate", type="primary", disabled=len(question.strip()) < 5):
    with st.spinner("Retrieving evidence and preparing an answer..."):
        try:
            response = requests.post(
                f"{API_URL}/questions/ask",
                json={"question": question},
                timeout=180,
            )
        except requests.RequestException as exc:
            st.error(f"Could not reach PaperTrail API: {exc}")
        else:
            if response.ok:
                result = response.json()
                st.markdown("### Answer")
                st.write(result["answer"])

                if result["limitations"]:
                    st.warning("Limitations: " + " ".join(result["limitations"]))

                st.markdown("### Retrieved evidence")
                for source in result["sources"]:
                    with st.expander(
                        f"[{source['source_id']}] {source['filename']} — page {source['page']}"
                    ):
                        st.write(source["excerpt"])
                        st.caption(f"Paper ID: {source['paper_id']}")
            else:
                st.error(response.text)

st.divider()
st.caption(
    "MVP limitation: citation-label validation does not prove that a passage supports "
    "the generated claim. Verify important conclusions manually."
)
