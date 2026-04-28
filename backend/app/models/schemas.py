"""
ReportMaster AI — Pydantic v2 Schemas
All request/response models used across the API layer.
"""

from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Payload for a user question directed at the financial manuals corpus."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The natural-language question to answer from the financial manuals.",
        examples=["What are the disclosure requirements under IFRS 17?"],
    )


# ── Response Models ───────────────────────────────────────────────────────────

class SourceDocument(BaseModel):
    """A single retrieved document chunk returned alongside an answer."""

    content: str = Field(..., description="Raw text content of the retrieved chunk.")
    doc_title: str = Field(..., description="Human-readable title of the source document.")
    chunk_index: int = Field(..., description="Zero-based index of this chunk within its parent document.")
    page_number: int | None = Field(None, description="The page number from the source document (if available).")
    score: float = Field(..., description="Cosine similarity score (0.0 – 1.0) for this chunk.")


class QueryResponse(BaseModel):
    """Full response returned after processing a user query."""

    answer: str = Field(..., description="LLM-generated answer grounded in the retrieved sources.")
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="Ordered list of source chunks used to produce the answer.",
    )
    query: str = Field(..., description="The original question as received by the API.")


class IngestResponse(BaseModel):
    """Response confirming that a data ingestion job has been triggered/completed."""

    message: str = Field(..., description="Human-readable status message.")
    documents_indexed: int = Field(
        ...,
        ge=0,
        description="Number of document chunks successfully indexed.",
    )


class HealthResponse(BaseModel):
    """Lightweight liveness/readiness probe response."""

    status: str = Field(..., description="Overall health status, e.g. 'ok' or 'degraded'.")
    collection_loaded: bool = Field(
        ...,
        description="Whether the ChromaDB collection is reachable and non-empty.",
    )


class StatsResponse(BaseModel):
    """Collection-level statistics returned by the /api/stats endpoint."""

    total_documents: int = Field(
        ...,
        ge=0,
        description="Total number of chunks currently stored in the vector collection.",
    )
    collection_name: str = Field(..., description="Name of the active ChromaDB collection.")
