"""
ReportMaster AI — Embedding Model
Phase 2 implementation using sentence-transformers.

Converts raw text strings into dense float vectors for semantic similarity search.
Used during both bulk ingestion (encoding thousands of chunks) and at query time
(encoding the user's single question before ChromaDB lookup).
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Wraps a sentence-transformers SentenceTransformer to produce dense vector
    embeddings suitable for cosine similarity search in ChromaDB.

    The model is loaded once at startup and reused for every embed() call,
    keeping inference latency low on repeated queries from accounting teams.
    """

    def __init__(self) -> None:
        """
        Load the sentence-transformers model specified in application settings.

        The model name (e.g. 'all-MiniLM-L6-v2') is read from
        settings.EMBEDDING_MODEL so it can be changed via environment variable
        without modifying source code.

        Raises:
            OSError: If the model name is invalid or cannot be downloaded.
        """
        from sentence_transformers import SentenceTransformer  # lazy import

        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print(f"Embedding model loaded: {settings.EMBEDDING_MODEL}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate vector embeddings for a list of financial document chunks.

        Used during both ingestion (bulk encoding of thousands of chunks from
        financial reporting manuals) and at query time (encoding the user's
        natural-language accounting question before ChromaDB lookup).

        Each embedding captures the semantic meaning of an accounting rule,
        disclosure requirement, or financial procedure — enabling retrieval by
        meaning rather than keyword matching.

        Args:
            texts: A list of raw text strings to embed. May be single sentences
                   or multi-sentence chunks up to settings.CHUNK_SIZE tokens.

        Returns:
            A list of float vectors, one per input text. Vector dimension is
            determined by the loaded model (384 for all-MiniLM-L6-v2).

        Raises:
            ValueError: If texts is empty.
            RuntimeError: If the underlying model inference fails.
        """
        if not texts:
            raise ValueError("embed() received an empty list of texts.")

        # encode() returns a numpy ndarray; convert to plain Python lists so
        # the output is JSON-serialisable and ChromaDB-compatible.
        vectors = self.model.encode(texts, show_progress_bar=False)
        return [vec.tolist() for vec in vectors]

    def embed_query(self, query: str) -> list[float]:
        """
        Encode a single natural-language query from an accounting team member.

        Convenience wrapper around embed() for the common single-string case
        at retrieval time. Avoids the caller needing to unpack a list.

        Args:
            query: A natural-language question such as
                   "What are the disclosure requirements under IFRS 17?"

        Returns:
            A single float vector of the same dimensionality as embed() output.

        Raises:
            ValueError: If query is an empty string.
        """
        if not query or not query.strip():
            raise ValueError("embed_query() received an empty query string.")

        return self.embed([query])[0]


# ── Module-level singleton ─────────────────────────────────────────────────────
# Instantiated once when the module is first imported so that both FastAPI
# (during requests) and the ingestion script share a single loaded model.
embedding_model = EmbeddingModel()
