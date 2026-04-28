"""
ReportMaster AI — RAG Pipeline (Phase 3)

Full Retrieval-Augmented Generation pipeline connecting ChromaDB semantic search
to OpenAI GPT-4o-mini for grounded, citation-backed answers to accounting questions.

Architecture:
  User question
      │
      ▼
  VectorStore.similarity_search()  ──►  Top-k chunks from ChromaDB
      │
      ▼
  build_context()                  ──►  Numbered context block for the prompt
      │
      ▼
  OpenAI GPT-4o-mini  (or Demo Mode) ──►  Grounded answer with inline citations
      │
      ▼
  QueryResponse(answer, sources, query)

Demo Mode (no OpenAI key):
  When OPENAI_API_KEY is not configured, the pipeline operates in Demo Mode:
  it synthesises a structured, citation-formatted answer directly from the
  top-scored retrieved chunks — no external API required.  The retrieval,
  embedding, and ChromaDB layers all run at full fidelity; only the LLM
  synthesis step is replaced with deterministic template rendering.
  Set a real OPENAI_API_KEY in .env to activate full GPT-4o-mini synthesis.

The pipeline enforces strict grounding: answers are always built from
retrieved context only, preventing hallucinations unsuitable for certified
accountants — in both LLM and Demo modes.
"""

from __future__ import annotations

import logging
import textwrap

from langchain_google_genai import ChatGoogleGenerativeAI
from fastapi import HTTPException

from app.core.config import settings
from app.models.schemas import QueryResponse, SourceDocument
from app.rag.vectorstore import vector_store

logger = logging.getLogger("reportmaster.pipeline")

# Sentinel value that ships in .env.example — signals demo mode
_DEMO_KEY_SENTINEL = "your_google_key_here"


def _is_demo_mode() -> bool:
    """
    Return True when no real Google API key has been configured.
    """
    key = (settings.GOOGLE_API_KEY or "").strip()
    return not key or key == _DEMO_KEY_SENTINEL

# ── Prompt Templates ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are ReportMaster AI, an expert assistant for internal financial reporting standards and accounting procedures.

STRICT GROUNDING RULES:
1. Use ONLY the provided context to answer questions. 
2. If the answer is not explicitly found in the context, you MUST respond exactly with: 
   "This information is not available in the current financial reporting manuals."
3. Do NOT use your general training data to answer. Do NOT guess or extrapolate.
4. If the context contains conflicting information, state that the manual has conflicting sections.
5. Always provide professional, clear, and concise answers suitable for an accounting department.

CITATION RULES:
- Every factual claim MUST be followed by a citation.
- Each context chunk starts with a bracketed header like `[Document: Name | Page: X]`. Use this information for precise citations.
- Format citations at the end of sentences or paragraphs using: [Source: <doc_title>, Page <page_number>].
- If you quote or reference information from multiple pages, cite all of them.
- Ensure the citation matches the document/page exactly as provided in the chunk header.

FORMATTING RULES:
1. Avoid using excessive markdown bolding (**text**). Use it only for critical terms or headers.
2. Use bullet points for lists to improve readability.
3. Keep paragraphs short and professional.
4. Do NOT use special characters or emojis unless requested.
5. If the answer is long, use simple, clear headings."""

USER_PROMPT_TEMPLATE = """INTERNAL MANUALS CONTEXT:
---
{context}
---

ACCOUNTING TEAM QUESTION:
{question}

Instructions: Provide a grounded answer based ONLY on the manuals above. Include specific citations for every point."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_context(sources: list[SourceDocument]) -> str:
    """
    Format retrieved ChromaDB chunks into a numbered context block for injection
    into the LLM prompt.

    Each entry is prefixed with a bracketed index number and labelled with the
    source document title and chunk index so the LLM can produce properly
    formatted inline citations (e.g. "[Source: Goldman Sachs, Section 2]").

    Args:
        sources: Ordered list of SourceDocument objects from similarity_search(),
                 best match first.

    Returns:
        A multi-line string ready to be substituted into USER_PROMPT_TEMPLATE.
    """
    lines: list[str] = []
    for i, doc in enumerate(sources):
        meta = f"Source: {doc.doc_title}"
        if doc.page_number:
            meta += f" | Page {doc.page_number}"
        else:
            meta += f" | Section {doc.chunk_index}"
        
        lines.append(f"[{i + 1}] {meta}")
        lines.append(f"    {doc.content}")
        lines.append("")  # blank separator between chunks
    return "\n".join(lines)


def _build_demo_answer(question: str, sources: list[SourceDocument]) -> str:
    """
    Synthesise a structured, citation-formatted answer from retrieved chunks
    without calling any external API.

    Used when OPENAI_API_KEY is not configured (Demo Mode).  The answer is
    entirely grounded in the ChromaDB results — no information is fabricated.
    Formatting mirrors what GPT-4o-mini would produce so the frontend renders
    identically in both modes.

    Strategy:
      • The top-scored chunk supplies the primary answer paragraph.
      • Additional chunks are appended as supplementary context.
      • Every sentence includes a [Source: …, Section …] citation.
      • A clear demo-mode notice is prepended so users know LLM synthesis
        is not active and explains how to enable it.

    Args:
        question: The original accounting question.
        sources:  Ordered list of retrieved SourceDocument objects.

    Returns:
        A plain-text answer string with inline citations, ready for the
        QueryResponse.answer field.
    """
    notice = (
        "[Demo Mode — set GOOGLE_API_KEY in backend/.env to enable Gemini synthesis]\n\n"
    )

    # Primary answer: top chunk (highest cosine similarity)
    top = sources[0]
    # Wrap long chunk text to ~100 chars per line for readability
    excerpt = textwrap.fill(top.content, width=120)
    primary = (
        f"Based on the most relevant section retrieved from the financial reporting knowledge base:\n\n"
        f"{excerpt}\n\n"
        f"[Source: {top.doc_title}, Section {top.chunk_index}]"
    )

    # Supplementary sources (chunks 2+)
    supplementary_parts: list[str] = []
    for doc in sources[1:]:
        short = textwrap.shorten(doc.content, width=200, placeholder="…")
        supplementary_parts.append(
            f"  • {short} "
            f"[Source: {doc.doc_title}, Section {doc.chunk_index}]"
        )

    supplementary = ""
    if supplementary_parts:
        supplementary = (
            "\n\nAdditional relevant context from the knowledge base:\n"
            + "\n".join(supplementary_parts)
        )

    return notice + primary + supplementary


# ── RAGPipeline ───────────────────────────────────────────────────────────────

class RAGPipeline:
    """
    Orchestrates the full Retrieval-Augmented Generation cycle for
    ReportMaster AI's financial reporting question-answering service.

    Lifecycle:
      • __init__       — binds the shared VectorStore singleton and creates an
                         async OpenAI client using the configured API key.
      • query()        — executes the 5-step RAG cycle (retrieve → context →
                         prompt → LLM → response) for a single accounting question.
      • query_with_fallback() — safe wrapper that surfaces graceful degradation
                         messages instead of unhandled 500 errors.
      • get_pipeline_status() — diagnostic snapshot used by /api/health and /api/stats.
    """

    def __init__(self) -> None:
        """
        Initialize the RAG pipeline for financial reporting manual retrieval.

        Loads the shared VectorStore singleton (already connected to ChromaDB)
        and creates a Gemini client so both are ready before the first
        query arrives.

        If GOOGLE_API_KEY is not set (or still the .env.example placeholder),
        the pipeline starts in Demo Mode.
        """
        self.vector_store = vector_store
        self.model = "gemini-1.5-flash"
        self.demo_mode = _is_demo_mode()

        if self.demo_mode:
            self.llm = None
            logger.warning(
                "RAGPipeline starting in DEMO MODE — "
                "no GOOGLE_API_KEY configured. "
                "Set a real key in backend/.env to enable LLM synthesis."
            )
            print("RAGPipeline initialized. [DEMO MODE — no Google key]")
        else:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-flash-latest",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,
            )
            logger.info("RAGPipeline initialised. LLM model: %s", "gemini-1.5-flash-latest")
            print(f"RAGPipeline initialized. [LLM: gemini-1.5-flash-latest]")

    # ── Core query method ─────────────────────────────────────────────────────

    async def query(self, question: str) -> QueryResponse:
        """
        Execute the full RAG pipeline for an accounting question.

        Steps:
          1. Retrieve top-k semantically relevant chunks from ChromaDB using
             cosine similarity on sentence-transformer embeddings.
          2. Assemble the retrieved chunks into a numbered context block with
             source labels for LLM citation.
          3. Construct a grounded prompt from the SYSTEM_PROMPT and
             USER_PROMPT_TEMPLATE constants.
          4. Call OpenAI GPT-4o-mini with temperature=0.1 for consistent,
             factual answers suitable for certified accountants.
          5. Return the answer alongside the full list of source chunks so the
             frontend can render citation cards.

        This method is the core intelligence of ReportMaster AI.
        Every answer is traceable back to a specific chunk in the ChromaDB index.

        Args:
            question: A natural-language question from an accounting team member,
                      e.g. "What are the revenue recognition criteria under ASC 606?"

        Returns:
            QueryResponse with answer text, source SourceDocument list, and
            the original question echoed back.

        Raises:
            HTTPException 503: If ChromaDB is empty (ingestion has not been run).
            HTTPException 502: If the OpenAI API call fails for any reason.
        """
        # ── Step 1: Retrieve relevant chunks ──────────────────────────────────
        logger.debug("Running similarity search for question: %.80s…", question)
        sources: list[SourceDocument] = self.vector_store.similarity_search(
            question, k=settings.TOP_K_RESULTS
        )

        if not sources:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Knowledge base is empty. "
                    "Please run the ingestion script first."
                ),
            )

        # ── Step 2: Build context string ──────────────────────────────────────
        context = build_context(sources)
        logger.debug("Context assembled from %d source chunks.", len(sources))

        # ── Step 3: Construct messages ────────────────────────────────────────
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    context=context,
                    question=question,
                ),
            },
        ]

        # ── Step 4: Call LLM  (or Demo Mode synthesis) ───────────────────────
        if self.demo_mode:
            # ── Demo Mode: synthesise answer from retrieved chunks ─────────────
            logger.info("Demo Mode: synthesising answer from %d chunks.", len(sources))
            answer = _build_demo_answer(question, sources)
        else:
            # ── LLM Mode: call Google Gemini ─────────────────────────────
            try:
                response = await self.llm.ainvoke(messages)
                content = response.content
                if isinstance(content, list):
                    # Handle multi-part content if returned
                    answer = "".join([str(c.get("text", "")) if isinstance(c, dict) else str(c) for c in content]).strip()
                else:
                    answer = str(content).strip()
                logger.debug("LLM response received (%d chars).", len(answer))

            except Exception as exc:
                logger.error("LLM API error: %s", exc)
                raise HTTPException(
                    status_code=502,
                    detail=f"LLM error: {str(exc)}",
                ) from exc

        # ── Step 5: Return QueryResponse ──────────────────────────────────────
        return QueryResponse(
            answer=answer,
            sources=sources,
            query=question,
        )

    # ── Fallback wrapper ──────────────────────────────────────────────────────

    async def query_with_fallback(self, question: str) -> QueryResponse:
        """
        Safe wrapper around query() that catches all unexpected errors and returns
        a graceful degradation message instead of crashing the API with a 500.

        Known HTTP errors (503 empty DB, 502 LLM failure) are re-raised as-is so
        the router can surface the correct status code to the client.

        Unexpected exceptions (e.g. network timeouts, ChromaDB connection drops)
        are caught and converted to a 200 response with an informative error message
        so the frontend chat UI always receives a parseable QueryResponse.

        Args:
            question: The original question string from the API request.

        Returns:
            QueryResponse — either the real RAG answer or a graceful error message.

        Raises:
            HTTPException: 503 or 502 from query() are re-raised unchanged.
        """
        try:
            return await self.query(question)
        except HTTPException:
            raise  # re-raise known HTTP errors (503, 502) unchanged
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error in RAG pipeline: %s", exc)
            return QueryResponse(
                answer=(
                    "An unexpected error occurred while processing your query. "
                    f"Please try again. (Error: {type(exc).__name__})"
                ),
                sources=[],
                query=question,
            )

    # ── Diagnostic ────────────────────────────────────────────────────────────

    def get_pipeline_status(self) -> dict:
        """
        Return a diagnostic snapshot of the pipeline's current state.

        Queries ChromaDB for the current document count to determine whether the
        knowledge base has been populated. Used by both the /api/health endpoint
        (readiness check) and /api/stats endpoint (frontend dashboard display).

        Returns:
            A dict with keys:
              collection_loaded (bool)  — True if count > 0
              total_documents   (int)   — current ChromaDB chunk count
              collection_name   (str)   — from settings
              embedding_model   (str)   — from settings
              llm_model         (str)   — hardcoded to self.model
        """
        try:
            count = self.vector_store.get_count()
            loaded = count > 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("VectorStore count check failed: %s", exc)
            count = 0
            loaded = False

        return {
            "collection_loaded": loaded,
            "total_documents": count,
            "collection_name": settings.COLLECTION_NAME,
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": self.model,
            "demo_mode": self.demo_mode,
        }


# ── Module-level singleton ─────────────────────────────────────────────────────
# Instantiated once when the module is first imported (during FastAPI startup).
# The singleton is shared by the router and the lifespan handler so there is
# never more than one OpenAI client or VectorStore connection at runtime.
rag_pipeline = RAGPipeline()
