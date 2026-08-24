# ReportMaster AI

**Financial Reporting Intelligence Hub** — a RAG assistant for asking questions about financial reporting manuals. Answers are grounded in retrieved chunks and returned with source citations.

**Live demo**

| | URL |
|---|---|
| App (Vercel) | [https://report-master-ai.vercel.app](https://report-master-ai.vercel.app) |
| API (Railway) | [https://reportmaster-ai-production.up.railway.app](https://reportmaster-ai-production.up.railway.app) |
| API health | [https://reportmaster-ai-production.up.railway.app/api/health](https://reportmaster-ai-production.up.railway.app/api/health) |

Sign up on the Vercel URL, then upload a **text** PDF (not a scan) before asking questions. An empty knowledge base returns `"collection_loaded": false`.

Full hosting steps: **[DEPLOY.md](DEPLOY.md)** (Vercel frontend + Railway backend).

---

## What it does

1. You create an account (JWT + bcrypt, users in SQLite).
2. You upload a PDF manual (or run a HuggingFace ingest script).
3. Text is chunked, embedded with MiniLM (`all-MiniLM-L6-v2`, 384-d), and stored in ChromaDB (cosine / HNSW).
4. A question is embedded the same way; the top 5 chunks are sent to **Google Gemini**.
5. The model is instructed to answer only from those chunks. The API also returns the chunks and similarity scores for the UI.

If `GOOGLE_API_KEY` is missing, **demo mode** still runs retrieval and builds an extractive answer from the top chunks.

---

## Architecture

```
React (Vercel or localhost:3000)
        │  Axios + Bearer JWT
        │  REACT_APP_API_URL → FastAPI
        ▼
FastAPI (Railway or localhost:8000)
        ├── /api/auth/*     → SQLite users
        ├── /api/query      → RAGPipeline
        │                      ├── EmbeddingModel (sentence-transformers)
        │                      ├── VectorStore (ChromaDB)
        │                      └── Gemini (or demo mode)
        └── /api/upload     → save PDF → ingest_manuals (resets collection)
```

```
reportmaster-ai/
├── backend/     # FastAPI + RAG + auth
├── frontend/    # React 18 + Tailwind
├── DEPLOY.md    # Vercel + Railway walkthrough
└── README.md
```

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router, Tailwind CSS v3, Axios, jwt-decode |
| Backend | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Auth | JWT (HS256), bcrypt, SQLAlchemy + SQLite |
| RAG | LangChain, `sentence-transformers` (`all-MiniLM-L6-v2`) |
| LLM | Google Gemini (`langchain-google-genai`) |
| Vector store | ChromaDB (disk; `/data/chroma_db` on Railway) |
| Ingest | HuggingFace `datasets` **or** local PDFs via `pypdf` |

---

## Status

| Area | Status |
|---|---|
| FastAPI app, schemas, CORS | Implemented |
| MiniLM embeddings + ChromaDB | Implemented |
| RAG pipeline + Gemini + demo mode | Implemented |
| JWT auth, login / signup / dashboard | Implemented |
| PDF upload + `ingest_manuals.py` | Implemented |
| HuggingFace ingest (`ingest_data.py`) | Implemented (wipes the same collection) |
| React chat UI, history, source cards | Implemented |
| Hosted Vercel + Railway | Configured — see [DEPLOY.md](DEPLOY.md) |
| Automated tests / CI | Not in this repo |

The two ingest paths **reset** the same Chroma collection. Use PDFs **or** the HuggingFace dataset, not both at once.

---

## Local development

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+
- A Gemini key from [Google AI Studio](https://aistudio.google.com/apikey) (optional; demo mode works without it)

### Backend

```bash
cd backend
cp .env.example .env
# Set GOOGLE_API_KEY and a real SECRET_KEY in .env
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: **http://localhost:8000**  
Docs: **http://localhost:8000/docs**

### Frontend

```bash
cd frontend
npm install
npm start
```

UI: **http://localhost:3000**

Axios uses `REACT_APP_API_URL` if set, otherwise `http://127.0.0.1:8000`. See `frontend/.env.example`.

### Seed the knowledge base

```bash
cd backend
python scripts/ingest_manuals.py    # PDFs in data/manuals
# or
python scripts/ingest_data.py       # HuggingFace financial-services dataset
```

From the UI (after login): **Upload Manual (PDF)**.

---

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Service ping |
| GET | `/api/health` | No | `{ status, collection_loaded }` |
| GET | `/api/stats` | JWT | Chunk count + collection name |
| POST | `/api/query` | JWT | `{ "question": "..." }` (3–500 chars) → answer + sources |
| POST | `/api/upload` | JWT | Multipart PDF; re-indexes all manuals (blocking) |
| POST | `/api/ingest` | **No** | Background HuggingFace ingest (`ingest_data.py`) |
| POST | `/api/auth/register` | No | `{ email, password }` |
| POST | `/api/auth/login` | No | OAuth2 form: `username` (email) + `password` → JWT |
| GET | `/api/auth/me` | JWT | Current user |

### Health check

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "ok",
  "collection_loaded": false
}
```

### Query (requires a token)

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the revenue recognition criteria under ASC 606?"}'
```

Response shape: `{ "answer": "...", "sources": [ { "content", "doc_title", "chunk_index", "page_number", "score" } ], "query": "..." }`.

Empty index → **503**. Gemini failure → **502**.

---

## Environment variables

Copy `backend/.env.example` → `backend/.env`. Do not commit `.env`.

| Variable | Default / local | Description |
|---|---|---|
| `GOOGLE_API_KEY` | placeholder | Gemini. Empty/placeholder → demo mode |
| `SECRET_KEY` | insecure default | JWT signing key — change in production |
| `DATABASE_URL` | `sqlite:///./data/reportmaster.db` | Users DB. Railway: `sqlite:////data/reportmaster.db` |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Vector index. Railway: `/data/chroma_db` |
| `MANUALS_DIR` | `backend/data/manuals` | Uploaded PDFs. Railway: `/data/manuals` |
| `COLLECTION_NAME` | `financial_manuals` | Chroma collection |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Must match at ingest and query |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per question |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `500` / `50` | **Characters** on the HuggingFace path (`RecursiveCharacterTextSplitter`). PDF ingest uses 800 / 100 |
| `CORS_ORIGINS` | `http://localhost:3000` | Read via `os.getenv` (not Pydantic). `*`, one origin, or comma-separated. Production: `https://report-master-ai.vercel.app` |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | 24 hours |

Frontend (Vercel / `frontend/.env`):

| Variable | Value |
|---|---|
| `REACT_APP_API_URL` | `https://reportmaster-ai-production.up.railway.app` (no trailing slash). Baked in at **build** time |

---

## Project structure

```
reportmaster-ai/
├── DEPLOY.md
├── README.md
├── backend/
│   ├── Procfile                 # Railway: uvicorn on $PORT
│   ├── railway.toml
│   ├── runtime.txt              # Python 3.11
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              # FastAPI, CORS, lifespan
│   │   ├── core/
│   │   │   ├── config.py        # Settings + get_cors_origin_list()
│   │   │   ├── database.py      # SQLAlchemy / DATABASE_URL
│   │   │   └── security.py      # bcrypt + JWT
│   │   ├── models/
│   │   │   ├── schemas.py       # Query / source Pydantic models
│   │   │   └── user.py          # users table
│   │   ├── routers/
│   │   │   ├── auth.py          # register, login, /me
│   │   │   ├── query.py         # query, health, stats, ingest
│   │   │   └── upload.py        # PDF upload
│   │   └── rag/
│   │       ├── pipeline.py      # retrieve → Gemini or demo
│   │       ├── embeddings.py
│   │       └── vectorstore.py
│   └── scripts/
│       ├── ingest_data.py       # HuggingFace dataset → Chroma
│       └── ingest_manuals.py    # PDFs → Chroma
└── frontend/
    ├── vercel.json              # SPA fallback for /login, /query, …
    ├── .env.example
    └── src/
        ├── App.jsx
        ├── context/AuthContext.jsx
        ├── pages/               # Login, Signup, Dashboard, ReportMaster
        ├── components/          # Chat, history, header, protected route
        └── services/api.js
```

---

## Deploy (Vercel + Railway)

| Piece | Host | Notes |
|---|---|---|
| Frontend | Vercel | Root directory **`frontend`**. Env: `REACT_APP_API_URL` |
| Backend | Railway | Root directory **`backend`**. ~**2 GB** RAM. Volume at **`/data`** |
| Users + vectors | Railway volume | SQLite + Chroma + PDF cache under `/data` |

Step-by-step (accounts, variables, CORS, troubleshooting): **[DEPLOY.md](DEPLOY.md)**.

Production CORS on Railway:

```
CORS_ORIGINS=https://report-master-ai.vercel.app
```

---

## Local verification

- [ ] `GET http://localhost:8000/` → `{"message": "ReportMaster AI is running"}`
- [ ] `GET http://localhost:8000/api/health` → `"status": "ok"`
- [ ] `npm start` → login page at http://localhost:3000
- [ ] Sign up → dashboard → upload a text PDF → ask a question
- [ ] `/api/query` without a JWT → **401**
- [ ] Query before ingest → **503**

---

## License

MIT © ReportMaster AI Team
