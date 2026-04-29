"""
ReportMaster AI — API Router (Phase 3)

Live FastAPI routes replacing the Phase 1 stubs.  All four endpoints are now
wired to the RAGPipeline singleton and return real data from ChromaDB and Gemini.

Route summary:
  POST /api/query   — Primary Q&A endpoint for the accounting team chat interface
  GET  /api/health  — Liveness/readiness probe for load balancers and monitoring
  POST /api/ingest  — Admin trigger for background re-ingestion of manuals
  GET  /api/stats   — Knowledge-base statistics for the frontend dashboard
"""

from __future__ import annotations

import logging
import subprocess
import sys

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.core.config import settings
from app.models.schemas import (
    HealthResponse,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    StatsResponse,
)
from app.rag.pipeline import rag_pipeline
from app.routers.auth import get_current_user
from app.models.user import User

logger = logging.getLogger("reportmaster.router")

router = APIRouter()


# ── POST /api/query ───────────────────────────────────────────────────────────

@router.post(
    "/api/query",
    response_model=QueryResponse,
    summary="Submit a financial reporting question",
    description=(
        "Primary endpoint for the accounting team Q&A interface. "
        "Accepts a natural-language question about financial reporting standards "
        "and returns a grounded answer with citations to specific manual sections. "
        "Returns 503 if the knowledge base has not been indexed yet. "
        "Returns 502 if the Gemini LLM call fails."
    ),
    tags=["Query"],
)
async def query_manuals(
    request: QueryRequest, current_user: User = Depends(get_current_user)
) -> QueryResponse:

    """
    Primary endpoint for the accounting team Q&A interface.

    Accepts a natural-language question about financial reporting standards
    and returns a grounded answer with citations to specific manual sections
    sourced from the ChromaDB vector index.

    The question is validated by Pydantic before reaching this handler:
      • min_length=3  → 422 Unprocessable Entity if too short
      • max_length=500 → 422 Unprocessable Entity if too long

    Args:
        request: QueryRequest containing the validated question string.

    Returns:
        QueryResponse with:
          answer   — LLM-generated text grounded in retrieved context
          sources  — ordered list of SourceDocument chunks used to produce answer
          query    — the original question echoed back for UI display

    Raises:
        HTTPException 503: Knowledge base is empty (ingestion not run yet).
        HTTPException 502: Gemini API call failed (rate limit, bad key, timeout).
    """
    logger.info("Query received: %.80s…", request.question)
    response = await rag_pipeline.query_with_fallback(request.question)
    logger.info(
        "Query answered. Answer length: %d chars. Sources: %d.",
        len(response.answer),
        len(response.sources),
    )
    return response


# ── GET /api/health ───────────────────────────────────────────────────────────

@router.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Liveness / readiness probe",
    description=(
        "Health check endpoint for load balancers, Kubernetes probes, and "
        "monitoring tools. Reports overall status and whether the ChromaDB "
        "collection is populated and ready to serve accounting queries."
    ),
    tags=["Operations"],
)
async def health_check() -> HealthResponse:
    """
    Liveness and readiness probe for the ReportMaster AI service.

    Queries the VectorStore for its current document count to determine
    whether the knowledge base has been populated.  A `collection_loaded: false`
    response indicates the ingestion script has not been run and the API will
    return 503 on any /api/query request.

    Returns:
        HealthResponse with:
          status            — always "ok" (service process is alive)
          collection_loaded — True only if ChromaDB contains at least one chunk
    """
    status = rag_pipeline.get_pipeline_status()
    return HealthResponse(
        status="ok",
        collection_loaded=status["collection_loaded"],
    )


# ── POST /api/ingest ──────────────────────────────────────────────────────────

@router.post(
    "/api/ingest",
    response_model=IngestResponse,
    summary="Trigger background re-ingestion of financial manuals",
    description=(
        "Admin endpoint to re-index the financial reporting manuals knowledge base. "
        "Launches scripts/ingest_data.py as a background subprocess so the API "
        "remains responsive during the (potentially long) ingestion run. "
        "Monitor progress in the server logs. "
        "Useful when the underlying HuggingFace dataset is updated with new "
        "accounting standards or when ChromaDB data is corrupted."
    ),
    tags=["Operations"],
)
async def trigger_ingest(background_tasks: BackgroundTasks) -> IngestResponse:
    """
    Trigger re-ingestion of financial reporting manuals as a background task.

    Runs scripts/ingest_data.py via subprocess so:
      1. The HTTP response is returned immediately (non-blocking).
      2. The ingestion pipeline (download → chunk → embed → index) runs in the
         background without blocking the FastAPI event loop.

    The ingestion script is idempotent: it resets the ChromaDB collection before
    re-indexing, so duplicate entries are never created on repeated calls.

    Returns:
        IngestResponse with a status message. documents_indexed is 0 because
        indexing is asynchronous; check /api/stats after completion.
    """
    def run_ingestion() -> None:
        """
        Background worker that executes the ingestion script as a subprocess.

        Captures both stdout and stderr; logs output at INFO level so progress
        is visible in the server log stream without blocking the async event loop.
        """
        logger.info("Background ingestion started.")
        result = subprocess.run(
            [sys.executable, "scripts/ingest_data.py"],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            logger.info("Ingestion output:\n%s", result.stdout)
        if result.returncode != 0:
            logger.error("Ingestion failed (exit %d):\n%s", result.returncode, result.stderr)
        else:
            logger.info("Background ingestion completed successfully.")

    background_tasks.add_task(run_ingestion)

    return IngestResponse(
        message=(
            "Ingestion triggered in background. "
            "Check server logs for progress."
        ),
        documents_indexed=0,
    )


# ── GET /api/stats ────────────────────────────────────────────────────────────

@router.get(
    "/api/stats",
    response_model=StatsResponse,
    summary="Knowledge-base statistics",
    description=(
        "Returns metadata about the current state of the financial manuals "
        "knowledge base — total indexed chunks and active collection name. "
        "Used by the frontend dashboard to display index status and guide "
        "accounting team members on data freshness."
    ),
    tags=["Operations"],
)
async def get_stats(current_user: User = Depends(get_current_user)) -> StatsResponse:

    """
    Return current statistics about the ChromaDB knowledge base.

    Retrieves the live document count directly from ChromaDB so the value is
    always accurate even after a background ingestion completes.  The frontend
    dashboard polls this endpoint to show how many manual chunks are available
    for semantic search.

    Returns:
        StatsResponse with:
          total_documents  — current number of chunks in ChromaDB collection
          collection_name  — name of the active ChromaDB collection
    """
    status = rag_pipeline.get_pipeline_status()
    return StatsResponse(
        total_documents=status["total_documents"],
        collection_name=status["collection_name"],
    )


# ── Developer Test Commands ───────────────────────────────────────────────────
#
# Run these from a terminal after starting the server with:
#   uvicorn app.main:app --reload
#
# Test 1 — valid query (requires ingestion + GOOGLE_API_KEY in .env)
# curl -X POST http://localhost:8000/api/query \
#   -H "Content-Type: application/json" \
#   -d '{"question": "What are the revenue recognition criteria under ASC 606?"}'
#
# Test 2 — health check
# curl http://localhost:8000/api/health
#
# Test 3 — stats
# curl http://localhost:8000/api/stats
#
# Test 4 — validation error (question too short → 422)
# curl -X POST http://localhost:8000/api/query \
#   -H "Content-Type: application/json" \
#   -d '{"question": "hi"}'
#
# Test 5 — trigger re-ingestion (runs in background)
# curl -X POST http://localhost:8000/api/ingest
#
# Test 6 — interactive API docs
# open http://localhost:8000/docs
