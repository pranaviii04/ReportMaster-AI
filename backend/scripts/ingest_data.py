"""
ReportMaster AI — Data Ingestion Pipeline
Phase 2 standalone script.

Loads the HuggingFace financial services dataset, chunks each company description
into overlapping windows, generates sentence-transformer embeddings, and persists
everything to a local ChromaDB collection so the Phase 3 RAG query pipeline can
perform semantic search at request time.

Dataset: ttn1410/financial_services_business_data
  • 488 records, single split: 'train'
  • Fields: ticker, name, sector, industry, country,
            market_cap, currency, employees, description
  • Primary text  → 'description'
  • Document title → 'name'  (company name, e.g. "Goldman Sachs Group, Inc.")
  • Extra metadata → ticker, sector, industry (surfaced in SourceCard)

Usage:
    cd backend
    python scripts/ingest_data.py
"""

from __future__ import annotations

import logging
import os
import sys

# ── Path bootstrap ─────────────────────────────────────────────────────────────
# Make `app` importable when the script is run from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Application imports (after path bootstrap) ─────────────────────────────────
from app.core.config import settings  # noqa: E402
from app.rag.embeddings import EmbeddingModel  # noqa: E402
from app.rag.vectorstore import VectorStore  # noqa: E402

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ingest_data")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load dataset
# ══════════════════════════════════════════════════════════════════════════════

def load_financial_dataset():
    """
    Load the financial services business dataset from HuggingFace Hub.

    This dataset contains structured data about publicly-listed financial
    services companies — including company descriptions that serve as the
    knowledge base for the ReportMaster AI reporting manual assistant.

    The dataset has a single split ('train') with 488 records.  Each record
    describes one company: its ticker, name, sector, industry, country,
    market cap, currency, employee count, and a free-text description.

    Returns:
        A HuggingFace Dataset object for the primary split.

    Raises:
        ConnectionError: If HuggingFace Hub is unreachable.
        datasets.exceptions.DatasetNotFoundError: If the dataset ID is wrong.
    """
    from datasets import load_dataset  # lazy — not needed at FastAPI startup

    print("Loading dataset from HuggingFace...")
    ds = load_dataset("ttn1410/financial_services_business_data")

    # Pick the split with the most records (robust to future dataset changes)
    split = max(ds.keys(), key=lambda s: len(ds[s]))
    data = ds[split]
    print(f"Loaded {len(data)} records from split: '{split}'")
    return data


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Extract and normalise records
# ══════════════════════════════════════════════════════════════════════════════

def extract_records(dataset) -> list[dict]:
    """
    Normalise raw HuggingFace dataset rows into clean dicts with a 'text' field
    and a 'metadata' dict ready for ChromaDB ingestion.

    Dataset schema (confirmed by inspection):
      • Primary text  → 'description'   (free-text company description)
      • Document title → 'name'          (company display name)
      • Extra metadata → 'ticker', 'sector', 'industry', 'country'

    Records with descriptions shorter than 20 characters are skipped because
    they contain no actionable financial information (e.g. "N/A", "—", empty).

    Args:
        dataset: A HuggingFace Dataset object from load_financial_dataset().

    Returns:
        List of dicts, each with keys 'text' and 'metadata'.

    Raises:
        KeyError: If the dataset is missing the expected 'description' field.
    """
    features = list(dataset.features.keys())
    logger.info("Dataset features: %s", features)

    # ── Detect primary text field ──────────────────────────────────────────────
    # Order reflects preference; 'description' is confirmed present in this dataset.
    TEXT_CANDIDATES = ["text", "content", "description", "instruction", "answer"]
    primary_field = next(
        (f for f in TEXT_CANDIDATES if f in features),
        None,
    )
    if primary_field is None:
        # Last-resort: use the first string-typed column
        from datasets import Value
        primary_field = next(
            f for f in features
            if isinstance(dataset.features[f], Value)
            and dataset.features[f].dtype == "string"
        )
        logger.warning(
            "No standard text field found; falling back to '%s'.", primary_field
        )

    # ── Detect title field ─────────────────────────────────────────────────────
    TITLE_CANDIDATES = ["name", "title", "category", "type", "label", "source"]
    title_field = next((f for f in TITLE_CANDIDATES if f in features), None)

    logger.info("Using text field: '%s', title field: '%s'", primary_field, title_field)

    # ── Additional metadata fields present in this dataset ────────────────────
    EXTRA_META = ["ticker", "sector", "industry", "country", "market_cap",
                  "currency", "employees"]
    extra_fields = [f for f in EXTRA_META if f in features]

    records: list[dict] = []
    skipped = 0

    for row in dataset:
        raw_text = str(row.get(primary_field, "") or "").strip()

        if len(raw_text) < 20:
            skipped += 1
            continue

        # Build doc_title: prefer explicit name field; fall back to text truncation
        if title_field and row.get(title_field):
            doc_title = str(row[title_field]).strip()
        else:
            doc_title = raw_text[:60] + "..."

        # Assemble metadata — include all available context for SourceCard display
        metadata: dict = {"doc_title": doc_title}
        for field in extra_fields:
            val = row.get(field)
            if val is not None:
                metadata[field] = str(val)

        records.append({"text": raw_text, "metadata": metadata})

    print(
        f"Extracted {len(records)} valid text records "
        f"(skipped {skipped} short/empty rows)"
    )
    return records


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Chunk documents
# ══════════════════════════════════════════════════════════════════════════════

def chunk_documents(records: list[dict]) -> list[dict]:
    """
    Split long financial company descriptions into overlapping text chunks for
    more precise semantic retrieval.

    Smaller chunks (settings.CHUNK_SIZE = 500 chars, overlap = 50 chars) allow
    ChromaDB to match a user's question against a specific accounting rule or
    procedure step rather than a broad multi-topic paragraph.

    The RecursiveCharacterTextSplitter tries paragraph breaks, then line breaks,
    then sentence boundaries, and finally word boundaries — so chunks stay
    semantically coherent rather than cutting mid-sentence.

    Args:
        records: List of dicts from extract_records(), each with 'text' and 'metadata'.

    Returns:
        List of chunk dicts, each with 'id', 'text', and 'metadata' keys.
        The metadata dict includes chunk_index and source_doc_index for tracing
        back to the original company record.

    Raises:
        ImportError: If langchain is not installed.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter  # lazy (langchain v0.2+)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []

    for i, record in enumerate(records):
        splits = splitter.split_text(record["text"])

        for j, chunk_text in enumerate(splits):
            chunks.append(
                {
                    "id": f"doc_{i}_chunk_{j}",
                    "text": chunk_text,
                    "metadata": {
                        **record["metadata"],
                        "chunk_index": j,
                        "source_doc_index": i,
                    },
                }
            )

    print(f"Chunked {len(records)} records into {len(chunks)} chunks")
    print(f"  chunk_size={settings.CHUNK_SIZE}, chunk_overlap={settings.CHUNK_OVERLAP}")
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Generate embeddings
# ══════════════════════════════════════════════════════════════════════════════

def generate_embeddings(chunks: list[dict], model: EmbeddingModel) -> list[dict]:
    """
    Generate sentence-transformer vector embeddings for each financial document chunk.

    Each 384-dimensional float vector captures the semantic meaning of a chunk —
    for example, embedding an IFRS revenue recognition paragraph close to the
    query "What are the revenue recognition criteria?" in vector space.

    Processes chunks in batches of 64 to balance memory usage and throughput on
    CPU-only hardware (typical for local development and CI environments).

    Args:
        chunks: List of chunk dicts from chunk_documents().
        model:  An EmbeddingModel instance whose embed() method accepts a list[str].

    Returns:
        The same list of chunk dicts with an 'embedding' key added to each,
        containing a list[float] of length equal to the model's output dimension.

    Raises:
        RuntimeError: If model.embed() fails for any batch.
    """
    BATCH_SIZE = 64
    total = len(chunks)

    print(f"Generating embeddings for {total} chunks (batch size: {BATCH_SIZE})...")

    all_texts = [c["text"] for c in chunks]
    all_embeddings: list[list[float]] = []

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch_texts = all_texts[start:end]

        try:
            vecs = model.embed(batch_texts)
        except Exception as exc:
            logger.error("Embedding failed for batch [%d:%d]: %s", start, end, exc)
            raise

        all_embeddings.extend(vecs)
        print(f"  [{end}/{total}] embeddings generated", end="\r")

    print()  # newline after progress line

    # Attach embedding to each chunk dict
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = all_embeddings[i]

    vec_dim = len(chunks[0]["embedding"]) if chunks else 0
    print(f"Embeddings complete. Vector dimension: {vec_dim}")
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Index to ChromaDB
# ══════════════════════════════════════════════════════════════════════════════

def index_to_chromadb(chunks: list[dict], store: VectorStore) -> None:
    """
    Persist all embedded chunks to the ChromaDB local persistent store.

    Resets the existing collection before adding new data to guarantee a clean
    index — essential when financial manuals are updated and re-ingested.

    Processes in batches of 256 to stay within ChromaDB's recommended per-call
    document limit and to allow progress reporting for large ingestion runs.

    Args:
        chunks: List of chunk dicts with 'id', 'text', 'embedding', 'metadata'.
        store:  A VectorStore instance connected to the configured collection.

    Raises:
        chromadb.errors.ChromaError: If any batch add() call fails.
    """
    BATCH_SIZE = 256
    total = len(chunks)

    print(f"Indexing {total} chunks to ChromaDB...")
    print(f"  Collection: '{settings.COLLECTION_NAME}'")
    print(f"  Persist directory: '{settings.CHROMA_PERSIST_DIR}'")

    # Wipe existing data so re-runs never produce duplicate-ID errors
    store.reset_collection()

    indexed = 0
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = chunks[start:end]

        try:
            store.add_documents(batch)
        except Exception as exc:
            logger.error(
                "ChromaDB add_documents failed for batch [%d:%d]: %s", start, end, exc
            )
            raise

        indexed += len(batch)
        print(f"  [{indexed}/{total}] chunks indexed", end="\r")

    print()  # newline after progress line

    final_count = store.get_count()
    print(f"Indexed to ChromaDB. Total documents in collection: {final_count}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Verification search
# ══════════════════════════════════════════════════════════════════════════════

def verify_retrieval(store: VectorStore) -> None:
    """
    Run a test semantic search query to confirm the ChromaDB index is operational.

    Uses a realistic question that an accounting team member might ask, verifying
    that the pipeline produces non-empty results with plausible relevance scores
    (between 0.0 and 1.0).  Logs a warning if no results are returned so the
    operator can diagnose ingestion failures without running the full pipeline again.

    Args:
        store: An initialised VectorStore with documents already indexed.
    """
    test_query = "What are the revenue recognition criteria for financial reporting?"
    print(f"\nVerification search: '{test_query}'")

    try:
        results = store.similarity_search(test_query, k=3)
    except Exception as exc:
        logger.error("Verification search failed: %s", exc)
        print(f"ERROR: Verification search raised an exception: {exc}")
        return

    if not results:
        print("WARNING: No results returned. Check ingestion logs above.")
        return

    for i, doc in enumerate(results):
        print(f"  [{i + 1}] Score: {doc.score:.4f} | Title: {doc.doc_title}")
        print(f"       Excerpt: {doc.content[:100]}...")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Orchestrate the full ReportMaster AI data ingestion pipeline.

    Runs all six steps in sequence:
      1. Load dataset from HuggingFace Hub
      2. Extract and normalise text records
      3. Chunk documents into overlapping windows
      4. Generate sentence-transformer embeddings
      5. Persist to ChromaDB with a clean-slate reset
      6. Run a verification semantic search

    Designed to be idempotent: re-running always produces a clean, correct index.
    """
    print("=" * 50)
    print("ReportMaster AI — Data Ingestion Pipeline")
    print("=" * 50)

    # Instantiate shared components
    model = EmbeddingModel()
    store = VectorStore()

    # Execute pipeline stages
    dataset = load_financial_dataset()
    records = extract_records(dataset)

    if not records:
        print("ERROR: No valid records extracted. Aborting ingestion.")
        sys.exit(1)

    chunks = chunk_documents(records)

    if not chunks:
        print("ERROR: No chunks produced. Aborting ingestion.")
        sys.exit(1)

    chunks = generate_embeddings(chunks, model)
    index_to_chromadb(chunks, store)
    verify_retrieval(store)

    print("\nIngestion complete. ReportMaster AI knowledge base is ready.")
    print("You can now start the FastAPI server and run Phase 3.")


if __name__ == "__main__":
    main()
