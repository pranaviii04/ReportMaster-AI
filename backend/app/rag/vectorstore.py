"""
ReportMaster AI — Vector Store (ChromaDB)
Phase 2 implementation of persistent semantic search over financial documents.

Wraps a ChromaDB PersistentClient and exposes add_documents(), similarity_search(),
get_count(), and reset_collection() so the ingestion script and FastAPI query router
can both operate on the same local vector index without re-embedding on every start.
"""

import logging
from app.core.config import settings
from app.models.schemas import SourceDocument

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Persistent ChromaDB-backed vector store for financial reporting manual chunks.

    ChromaDB stores:
      • The raw chunk text (documents)
      • The sentence-transformer embedding (embeddings)
      • Metadata (doc_title, chunk_index, source_doc_index)

    Cosine similarity is configured at the collection level so ChromaDB's HNSW
    index uses the correct distance metric for sentence-transformer embeddings.
    """

    def __init__(self) -> None:
        """
        Initialize the persistent ChromaDB client and attach to the configured
        collection for financial reporting manuals.

        Uses local disk persistence (settings.CHROMA_PERSIST_DIR) so the index
        survives server restarts and does not need to be rebuilt on every boot.
        The collection is created on first run and reloaded on subsequent runs.

        Raises:
            chromadb.errors.ChromaError: If the persistence directory is
                inaccessible or the collection metadata is corrupt.
        """
        import chromadb  # lazy import — not needed if only schemas are loaded

        logger.info(
            "Initialising VectorStore. persist_dir=%s collection=%s",
            settings.CHROMA_PERSIST_DIR,
            settings.COLLECTION_NAME,
        )

        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"VectorStore ready. Collection: '{settings.COLLECTION_NAME}'")

    # ── Write Operations ───────────────────────────────────────────────────────

    def add_documents(self, documents: list[dict]) -> int:
        """
        Index a batch of financial document chunks into ChromaDB.

        Each dict in `documents` must contain:
          • id         (str)          — unique chunk identifier, e.g. "doc_0_chunk_3"
          • text       (str)          — raw chunk text
          • embedding  (list[float])  — pre-computed sentence-transformer vector
          • metadata   (dict)         — at minimum {"doc_title": ..., "chunk_index": ...}

        Batching is handled by the caller (ingestion script) so this method
        simply passes the batch straight through to ChromaDB's add() API.

        Args:
            documents: List of chunk dicts as described above.

        Returns:
            Number of documents successfully passed to ChromaDB (len(documents)).

        Raises:
            chromadb.errors.DuplicateIDError: If any id already exists in the
                collection (caller should call reset_collection() first on re-ingestion).
            ValueError: If documents is empty or any dict is missing required keys.
        """
        if not documents:
            raise ValueError("add_documents() received an empty documents list.")

        ids = [d["id"] for d in documents]
        embeddings = [d["embedding"] for d in documents]
        texts = [d["text"] for d in documents]
        metadatas = [d["metadata"] for d in documents]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(documents)

    # ── Read Operations ────────────────────────────────────────────────────────

    def similarity_search(
        self, query: str, k: int | None = None
    ) -> list[SourceDocument]:
        """
        Retrieve the top-k most semantically relevant chunks for an accounting question.

        Converts the query string to a vector using the shared EmbeddingModel singleton,
        then asks ChromaDB to return the nearest neighbours by cosine similarity.

        ChromaDB returns *cosine distances* (0 = identical, 2 = opposite), which are
        converted to similarity scores (1 - distance) so that higher is always better,
        matching the intuition of accounting teams reviewing sources.

        Args:
            query: A natural-language question, e.g.
                   "What are the revenue recognition criteria under IFRS 15?"
            k:     Number of chunks to retrieve. Defaults to settings.TOP_K_RESULTS.

        Returns:
            List of SourceDocument objects ordered by descending relevance score.
            Returns an empty list if the collection is empty.

        Raises:
            RuntimeError: If ChromaDB query fails.
        """
        # Lazy import avoids circular dependency at module load time
        from app.rag.embeddings import embedding_model

        if k is None:
            k = settings.TOP_K_RESULTS

        # Guard: ChromaDB raises if n_results > collection size
        count = self.get_count()
        if count == 0:
            logger.warning("similarity_search called on an empty collection.")
            return []

        effective_k = min(k, count)

        query_vec = embedding_model.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=effective_k,
            include=["documents", "metadatas", "distances"],
        )

        source_docs: list[SourceDocument] = []
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metadatas, distances):
            # Cosine distance → similarity: clamp to [0, 1] to handle float drift
            similarity = round(max(0.0, min(1.0, 1.0 - dist)), 4)
            source_docs.append(
                SourceDocument(
                    content=doc,
                    doc_title=meta.get("doc_title", "Unknown"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=similarity,
                )
            )

        return source_docs

    def get_count(self) -> int:
        """
        Return the total number of indexed financial document chunks.

        Used by the /api/stats endpoint and the ingestion script to confirm
        that all expected chunks were persisted to ChromaDB successfully.

        Returns:
            Integer count of documents currently in the collection.
        """
        return self.collection.count()

    # ── Admin Operations ───────────────────────────────────────────────────────

    def reset_collection(self) -> None:
        """
        Delete and recreate the ChromaDB collection from scratch.

        Called at the start of every ingestion run to prevent duplicate-ID errors
        when financial manuals are updated and need to be re-indexed. All existing
        embeddings and metadata are permanently removed before new data is added.

        After reset, the collection exists but is empty (count == 0).
        """
        import chromadb  # re-import in case of lazy path

        logger.info("Resetting collection '%s'.", settings.COLLECTION_NAME)
        self.client.delete_collection(settings.COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print("Collection reset complete.")


# ── Module-level singleton ─────────────────────────────────────────────────────
# Instantiated once when the module is first imported.  FastAPI startup and the
# ingestion script both import this singleton rather than creating their own
# ChromaDB connections, keeping the persistent client single-instance.
vector_store = VectorStore()
