# PaperTrail — MVP

PaperTrail is an evidence-grounded research assistant for comparing and interrogating research papers.
This MVP supports PDF ingestion, page-aware retrieval, cited question answering, and a basic Streamlit UI.

## What is in scope

- Upload text-based research PDFs.
- Extract text while retaining paper and page metadata.
- Chunk and embed passages into a persistent local Chroma database.
- Ask questions across uploaded papers.
- Generate answers grounded in retrieved passages.
- Check citation-label integrity and return source excerpts (not semantic proof).

## Explicitly out of scope for MVP 1

- Autonomous web research or browsing.
- Fully autonomous multi-agent workflows.
- Guaranteed scientific fact-checking.
- OCR for scanned PDFs.
- Automated contradiction detection across papers.
- User accounts and cloud deployment.

These are later milestones. The goal is a small, testable product—not an elaborate agent diagram.

## Architecture

```text
                 Streamlit UI
                /            \
       Upload PDF            Ask question
           |                      |
           v                      v
      FastAPI API             FastAPI API
           |                      |
     PyMuPDF extraction       LangGraph workflow
           |                      |
     Page-aware chunks        1. Retrieve passages
           |                  2. Draft grounded answer
     Embeddings + Chroma      3. Validate citations
           |                      |
     Persistent local DB      Answer + source excerpts
```

### LangGraph state

`question -> retrieved_documents -> draft -> citation_check -> response`

There is one workflow with deterministic tools and explicit state. No separate LLM agents are needed for the first version.

## Stack

- Python 3.11+
- FastAPI — API
- Streamlit — lightweight UI
- LangGraph — workflow orchestration
- OpenRouter — LLM answer generation through an OpenAI-compatible API
- Sentence Transformers — local embeddings (no embedding API)
- Chroma — local persistent vector database
- PyMuPDF — PDF text extraction
- pytest — tests

## Run locally

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```

Put your OpenRouter API key in `.env`, then start the API. The local Sentence Transformers model downloads the first time it is used; allow time and disk space for that download:

```bash
uvicorn app.main:app --reload
```

In a second terminal, activate the same virtual environment and run:

```bash
streamlit run ui.py
```

Open the Streamlit URL shown in the terminal. FastAPI docs are at `http://127.0.0.1:8000/docs`.

## First demo

1. Upload two papers on the same topic.
2. Ask: "What evidence do these papers provide for their main claims?"
3. Ask: "Where do the papers disagree?"
4. Inspect the page citations and excerpts before trusting the answer.

The second question does not mean contradiction detection is solved. The model is asked to identify possible disagreement from retrieved evidence; verify its output against the cited passages.

## Environment variables

See `.env.example`. Set `OPENROUTER_API_KEY`; embeddings use `EMBEDDING_MODEL` locally. Do not commit `.env`. The `openrouter/free` router selects an available free model, so availability and rate limits can vary.

## Project structure

```text
papertrail/
├── app/
│   ├── config.py
│   ├── graph.py
│   ├── ingestion.py
│   ├── main.py
│   ├── schemas.py
│   └── store.py
├── data/
│   └── chroma/              # created automatically; do not commit
├── tests/
│   └── test_ingestion.py
├── .env.example
├── .gitignore
├── requirements.txt
└── ui.py
```

## Development milestones

1. Make upload and cited Q&A work locally.
2. Add a structured claim extractor (`claim`, `evidence`, `paper`, `page`).
3. Add cross-paper comparison and label results as `supports`, `contradicts`, or `insufficient evidence`.
4. Build a small evaluation set of 30–50 questions with expected source pages.
5. Measure retrieval hit rate, citation validity, answer faithfulness, latency, and cost.
6. Add Docker and deploy only after local evaluation is stable.

## Important limitations

- PDF extraction can fail on scanned PDFs, complex tables, and multi-column layouts.
- Similarity retrieval can miss relevant passages.
- Citation-label validation only checks that a cited label was retrieved; it does not prove that the passage semantically supports the sentence. Human review and a dedicated evaluation set are still necessary.
- Chroma is local and intended for this MVP, not a multi-user production deployment.

## Provider setup (OpenRouter + local embeddings)

PaperTrail separates the language model from the embedding model. OpenRouter handles answer generation; Sentence Transformers creates document and query vectors on your machine. You can change the LLM provider (for example, Gemini) without changing local embeddings. Conversely, you can use Gemini embeddings instead, but that is a separate embedding-provider configuration and is no longer fully local.

The first local embedding run downloads `all-MiniLM-L6-v2`. It uses your CPU by default and does not call OpenRouter. The initial download and embedding process use local disk, RAM, and CPU. Existing Chroma data created with another embedding model should be re-indexed into a fresh collection because vector dimensions and embedding spaces may differ.

## Review notes (MVP 0.1.1)

The reviewed version streams uploads to a temporary file with a 25 MB cap, keeps
blocking embedding/indexing work off FastAPI's event loop, logs internal exceptions
without exposing raw exception details to API clients, and handles a stopped backend
in the Streamlit UI.

This remains a learning MVP. It has no authentication, rate limiting, OCR, document
deletion, or semantic citation-entailment check. Do not expose it publicly or use its
answers as authoritative scientific conclusions.
