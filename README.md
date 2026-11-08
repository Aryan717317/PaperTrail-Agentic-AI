# PaperTrail — AI-Powered Research Intelligence & Evidence Verification Platform

PaperTrail is an evidence-grounded research assistant designed to transform collections of academic research papers into searchable, comparable, and verifiable knowledge.

Unlike conventional PDF chatbots that merely retrieve text passages, PaperTrail extracts structured claims, compares methodologies and experimental conditions, detects contradictions, evaluates evidence strength, and provides page-level traceable citations.

---

## Architecture & Technology Stack

| Component | Technology | Responsibility | Execution |
|---|---|---|---|
| **Frontend** | Streamlit | Research dashboard, paper selector, comparative tabs | Local |
| **Backend API** | FastAPI | REST API, async ingestion, document lifecycle | Local |
| **PDF Extraction** | PyMuPDF | Page-by-page text extraction with metadata | Local |
| **Ingestion Pipeline** | Cleaner + Recursive Chunker | Heuristic cleanup & boundary-aware chunking | Local |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Semantic representations (384-dim) | Local CPU |
| **Vector Database** | ChromaDB | Persistent local similarity search & deduplication | Local disk |
| **Orchestration** | LangGraph | Stateful workflow with sufficiency branching | Local |
| **Reasoning LLM** | OpenRouter (`openrouter/free`) | Synthesis, claim extraction & contradiction check | Remote API |

---

## Modular Directory Structure

```text
papertrail/
├── app/
│   ├── config.py                 # Pydantic Settings & environment configuration
│   ├── main.py                   # FastAPI application mounting modular routers
│   ├── schemas.py                # Request and response models
│   ├── api/
│   │   ├── health.py             # Health check endpoint
│   │   ├── documents.py          # Upload, list, and delete papers
│   │   └── research.py           # Q&A, claims, comparison, contradictions, evidence
│   ├── ingestion/
│   │   ├── pdf_extractor.py      # PyMuPDF page-aware extraction
│   │   ├── cleaner.py            # Header/footer & whitespace normalization
│   │   └── chunker.py            # Sentence-aware chunker with chunk_id hashing
│   ├── embeddings/
│   │   └── model.py              # Singleton local SentenceTransformer embeddings
│   ├── vectorstore/
│   │   └── chroma_store.py       # Persistent ChromaDB store with deduplication
│   ├── llm/
│   │   └── openrouter_client.py  # Cached OpenRouter ChatOpenAI client
│   ├── graph/
│   │   ├── state.py              # TypedDict research state
│   │   ├── nodes.py              # Retrieval, sufficiency, answer & citation nodes
│   │   └── workflow.py           # LangGraph StateGraph with conditional branching
│   ├── research/
│   │   ├── claim_extractor.py    # Structured academic claim extraction
│   │   ├── comparison.py         # Multi-paper matrix & divergent conditions
│   │   ├── contradiction.py      # Disagreement analysis & classification
│   │   └── evidence.py           # Directness of support & limitation evaluator
│   └── services/
│       └── document_service.py   # Document ingestion lifecycle & management
├── tests/
│   ├── fixtures/
│   │   └── sample_paper.pdf      # Valid PDF fixture for testing
│   ├── test_api.py               # REST API endpoints & lifecycle tests
│   ├── test_config.py            # Configuration defaults tests
│   ├── test_graph.py             # LangGraph routing & citation check tests
│   ├── test_ingestion.py         # Cleaner, chunker & PDF extractor tests
│   ├── test_research.py          # Schemas & data structures tests
│   └── test_vectorstore.py       # ChromaDB indexing, dedup & deletion tests
├── ui.py                         # Multi-tab Streamlit user interface
├── requirements.txt              # Pinned, tested dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Documentation
```

---

## Features Implemented

### 1. Evidence-Grounded Multi-Document RAG
- Users can upload multiple academic research papers.
- Ingestion streams files up to 25 MB with cleanup of headers, footers, and redundant line breaks.
- Chunks preserve `paper_id`, `filename`, `page`, and content-hashed `chunk_id` for duplicate prevention.
- Retrieval queries persistent ChromaDB collections with optional paper filtering.

### 2. LangGraph Stateful Orchestration
- **Conditional Branching:** Assesses whether retrieved evidence is sufficient.
  - If sufficient: drafts grounded answer citing `[S1]`, `[S2]` source labels.
  - If insufficient: explicitly abstains without hallucinating.
- **Citation Label Integrity Check:** Validates that cited references match actual retrieved sources.

### 3. Structured Research Claim Extraction
- Categorizes findings into: `hypothesis`, `experimental_finding`, `methodological_claim`, `performance_claim`, `limitation`, and `future_work`.
- Extracts methodology, metric, score, page number, and direct verbatim quote.

### 4. Cross-Paper Comparison Matrix
- Generates side-by-side comparisons of methodologies, datasets, benchmarks, metrics, and limitations.
- Highlights differences in experimental conditions (e.g. dataset domain, evaluation metric) rather than naively ranking numerical scores.

### 5. Contradiction & Disagreement Detection
- Evaluates relationships: `direct_contradiction`, `partial_disagreement`, `context_dependent`, `compatible`, or `insufficient_evidence`.
- Explains the divergence and underlying factors.

### 6. Evidence Quality Assessment
- Classifies degree of support: `direct`, `indirect`, `extrapolated`, or `unsupported`.
- Surfaces reported caveats, limitations, and supporting excerpts.

### 7. Document Lifecycle Management
- View all currently indexed papers with chunk counts.
- Delete specific papers from the vector store on demand.
- Selectively query subsets of indexed papers.

---

## Getting Started

### 1. Setup Virtual Environment
```bash
# Windows PowerShell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1

# Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free OpenRouter API key:
```env
OPENROUTER_API_KEY=your_actual_key_here
OPENROUTER_MODEL=openrouter/free
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 3. Run Automated Tests
```bash
.venv\Scripts\python.exe -m pytest -v
```
All 20 unit and integration tests run offline without consuming API credits.

### 4. Launch Backend API
```bash
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
Interactive Swagger API documentation: `http://127.0.0.1:8000/docs`

### 5. Launch Streamlit UI
In a separate terminal:
```bash
.venv\Scripts\streamlit.exe run ui.py
```
Open the local URL displayed in the terminal (typically `http://localhost:8501`).
