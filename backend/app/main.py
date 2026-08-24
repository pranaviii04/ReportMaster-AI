"""
ReportMaster AI — FastAPI Application Entry Point
Sets up CORS, lifespan events, and mounts all routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_cors_origin_list, settings
from app.routers.query import router as query_router
from app.routers.upload import router as upload_router
from app.routers.auth import router as auth_router
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application startup: warm up the RAG pipeline and verify the
    knowledge base is accessible before accepting any requests.

    Imports the rag_pipeline singleton (which in turn loads the EmbeddingModel
    and VectorStore singletons) so all heavy initialisation — model loading,
    ChromaDB client creation — happens at boot time rather than on the first
    query, eliminating cold-start latency for accounting team members.

    Logs a WARNING if the ChromaDB collection is empty, directing operators to
    run the ingestion script before the service will be able to answer questions.

    Shutdown:
        Prints a clean shutdown message.  ChromaDB PersistentClient flushes
        pending writes automatically when garbage collected.
    """
    print("ReportMaster AI starting up...")

    # Import triggers singleton instantiation: EmbeddingModel + VectorStore + Gemini client
    from app.rag.pipeline import rag_pipeline  # noqa: PLC0415

    status = rag_pipeline.get_pipeline_status()
    if status["collection_loaded"]:
        print(f"Knowledge base ready: {status['total_documents']} chunks indexed.")
    else:
        print("WARNING: Knowledge base is empty. Run scripts/ingest_data.py first.")

    print("ReportMaster AI is ready to serve queries.")
    yield
    print("ReportMaster AI shutting down.")


# ── Application Factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="ReportMaster AI",
    version="0.1.0",
    description=(
        "Financial Reporting Intelligence Hub — "
        "a RAG-powered assistant for querying financial reporting manuals."
    ),
    contact={
        "name": "ReportMaster AI Team",
        "url": "http://localhost:8000",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────────────────────

_cors_origins = get_cors_origin_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # Browsers reject allow_origins=["*"] combined with credentials=True.
    allow_credentials="*" not in _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(query_router)
app.include_router(upload_router)
app.include_router(auth_router)


# ── Root Route ────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"], summary="Root health ping")
async def root() -> dict[str, str]:
    """Simple root endpoint confirming the service is alive."""
    return {"message": "ReportMaster AI is running"}
