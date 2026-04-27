# ReportMaster AI 🧾

**Financial Reporting Intelligence Hub** — A RAG-powered assistant for querying financial reporting manuals using semantic search and large language models.

---

## Architecture Overview

```
reportmaster-ai/
├── backend/          # FastAPI + LangChain RAG service
└── frontend/         # React 18 + Tailwind CSS UI
```

```
User Query
    │
    ▼
React Frontend  ──POST /api/query──►  FastAPI Backend
                                          │
                                    RAGPipeline
                                    ├── EmbeddingModel  (sentence-transformers)
                                    ├── VectorStore     (ChromaDB)
                                    └── LLM Chain       (LangChain + OpenAI)
                                          │
                                    QueryResponse  (answer + sources)
```

---

## Tech Stack

| Layer      | Technology                                       |
|------------|--------------------------------------------------|
| Backend    | Python 3.11+, FastAPI, Pydantic v2, Uvicorn      |
| RAG        | LangChain, OpenAI GPT-4o, sentence-transformers  |
| Vector DB  | ChromaDB (local persistent store)                |
| Dataset    | HuggingFace `datasets` library                   |
| Frontend   | React 18, Tailwind CSS v3, Axios                 |

---

## Phase Roadmap

| Phase | Description                                      | Status        |
|-------|--------------------------------------------------|---------------|
| 1     | Project scaffold (this phase)                    | ✅ Complete   |
| 2     | Embeddings + ChromaDB integration                | ⏳ Pending    |
| 3     | LangChain RAG pipeline + OpenAI LLM              | ⏳ Pending    |
| 4     | Full React UI with state, history, source cards  | ⏳ Pending    |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

---

### Backend Setup

```bash
cd backend

# 1. Copy environment template and fill in your OpenAI key
cp .env.example .env

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the development server
uvicorn app.main:app --reload
```

The API will be available at **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

---

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the development server
npm start
```

The React app will be available at **http://localhost:3000**

---

## API Endpoints

| Method | Path          | Description                          |
|--------|---------------|--------------------------------------|
| GET    | `/`           | Root health ping                     |
| GET    | `/api/health` | Liveness / readiness probe           |
| GET    | `/api/stats`  | Vector store statistics              |
| POST   | `/api/query`  | Submit a financial reporting question|
| POST   | `/api/ingest` | Trigger document ingestion           |

### Example — Health Check

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "collection_loaded": false
}
```

### Example — Query (Phase 1 stub response)

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the disclosure requirements under IFRS 17?"}'
```

```json
{
  "answer": "Not implemented",
  "sources": [],
  "query": "What are the disclosure requirements under IFRS 17?"
}
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable              | Default                      | Description                           |
|-----------------------|------------------------------|---------------------------------------|
| `OPENAI_API_KEY`      | *(required in Phase 3)*      | OpenAI API key for LLM inference      |
| `CHROMA_PERSIST_DIR`  | `./chroma_db`                | Path to ChromaDB persistence directory|
| `COLLECTION_NAME`     | `financial_manuals`          | ChromaDB collection name              |
| `EMBEDDING_MODEL`     | `all-MiniLM-L6-v2`           | HuggingFace sentence-transformers model|
| `TOP_K_RESULTS`       | `5`                          | Number of chunks to retrieve per query|
| `CHUNK_SIZE`          | `500`                        | Tokens per document chunk             |
| `CHUNK_OVERLAP`       | `50`                         | Overlap tokens between adjacent chunks|
| `CORS_ORIGINS`        | `http://localhost:3000`      | Allowed CORS origins (comma-separated)|

---

## Project Structure — Detailed

```
reportmaster-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory + CORS + lifespan
│   │   ├── core/
│   │   │   └── config.py        # Pydantic BaseSettings — loads .env
│   │   ├── models/
│   │   │   └── schemas.py       # All Pydantic v2 request/response schemas
│   │   ├── routers/
│   │   │   └── query.py         # 4 API endpoints (stubs in Phase 1)
│   │   └── rag/
│   │       ├── pipeline.py      # RAGPipeline (stub → Phase 3)
│   │       ├── embeddings.py    # EmbeddingModel (stub → Phase 2)
│   │       └── vectorstore.py   # VectorStore (stub → Phase 2)
│   ├── scripts/
│   │   └── ingest_data.py       # Ingestion script (stub → Phase 2)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx           # Top nav bar
│   │   │   ├── ChatInterface.jsx    # Main Q&A panel
│   │   │   ├── SourceCard.jsx       # Retrieved chunk card
│   │   │   ├── QueryHistory.jsx     # Left sidebar history
│   │   │   └── LoadingIndicator.jsx # Skeleton animation
│   │   ├── services/
│   │   │   └── api.js               # Axios instance + API functions
│   │   ├── App.jsx                  # Root layout shell
│   │   ├── index.js                 # React 18 createRoot entry
│   │   └── index.css                # Tailwind directives + base styles
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
└── README.md
```

---

## Verification Checklist

After setup, confirm these endpoints all respond correctly:

- [ ] `GET  http://localhost:8000/`           → `{"message": "ReportMaster AI is running"}`
- [ ] `GET  http://localhost:8000/api/health` → `{"status": "ok", "collection_loaded": false}`
- [ ] `GET  http://localhost:8000/api/stats`  → `{"total_documents": 0, "collection_name": "financial_manuals"}`
- [ ] `POST http://localhost:8000/api/query`  → stub `QueryResponse`
- [ ] `POST http://localhost:8000/api/ingest` → stub `IngestResponse`
- [ ] `npm start` compiles and renders Header + ChatInterface without errors

---

## License

MIT © ReportMaster AI Team
