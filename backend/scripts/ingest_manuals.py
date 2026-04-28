"""
ReportMaster AI — PDF Manual Ingestion Pipeline
Phase 4 script for production use.

Scans the backend/data/manuals directory for PDF files, extracts their content,
chunks it into semantic windows, generates embeddings, and indexes them into
ChromaDB for retrieval.

Usage:
    cd backend
    python scripts/ingest_manuals.py
"""

import logging
import os
import sys
from pathlib import Path

# ── Path bootstrap ─────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Application imports ────────────────────────────────────────────────────────
from app.core.config import settings
from app.rag.embeddings import embedding_model
from app.rag.vectorstore import vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("ingest_manuals")


def extract_pdf_content(pdf_path: Path) -> list[dict]:
    """
    Extract text from a PDF file page by page.
    Returns a list of dicts: {"text": str, "metadata": {"page": int, "source": str}}
    """
    logger.info("Processing PDF: %s", pdf_path.name)
    pages = []
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 20:
                pages.append({
                    "text": text.strip(),
                    "metadata": {
                        "doc_title": pdf_path.name,
                        "page_number": i + 1,
                        "source": pdf_path.name
                    }
                })
    except Exception as exc:
        logger.error("Failed to read PDF %s: %s", pdf_path, exc)
    
    return pages


def run_ingestion() -> int:
    """
    Core ingestion logic that can be called from CLI or API.
    Returns the number of documents indexed.
    """
    manuals_path = Path(settings.MANUALS_DIR)
    if not manuals_path.exists():
        logger.error("Manuals directory not found: %s", manuals_path)
        return 0

    pdf_files = list(manuals_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", manuals_path)
        return 0

    logger.info("Found %d PDF(s). Starting extraction...", len(pdf_files))

    all_pages = []
    for pdf in pdf_files:
        all_pages.extend(extract_pdf_content(pdf))

    if not all_pages:
        logger.warning("No readable text found in the provided PDFs.")
        return 0

    logger.info("Extracted %d pages. Splitting into chunks...", len(all_pages))

    # Initialize splitter with slightly larger chunks for better context
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Increased from 500
        chunk_overlap=100, # Increased from 50
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []
    for i, page in enumerate(all_pages):
        splits = splitter.split_text(page["text"])
        for j, chunk_text in enumerate(splits):
            # Data Quality Improvement: Add source context to each chunk
            # This helps the model understand which document it's looking at
            # even if the citation instruction is missed.
            context_prefix = f"[Document: {page['metadata']['doc_title']} | Page: {page['metadata']['page_number']}]\n"
            enriched_text = context_prefix + chunk_text
            
            chunks.append({
                "id": f"manual_{i}_chunk_{j}",
                "text": enriched_text,
                "metadata": {
                    **page["metadata"],
                    "chunk_index": j,
                }
            })

    logger.info("Produced %d chunks.", len(chunks))
    
    # We reset the collection to ensure we only have the current manuals
    vector_store.reset_collection()

    # Process in batches
    BATCH_SIZE = 50
    total = len(chunks)
    
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = chunks[start:end]
        
        texts = [c["text"] for c in batch]
        embeddings = embedding_model.embed(texts)
        
        for k, chunk in enumerate(batch):
            chunk["embedding"] = embeddings[k]
        
        vector_store.add_documents(batch)
        logger.info("Indexed %d/%d chunks...", end, total)

    return total


def main():
    print("=" * 60)
    print("ReportMaster AI — Internal Manual Ingestion")
    print("=" * 60)
    
    total = run_ingestion()
    
    if total > 0:
        print(f"\nSuccessfully indexed {total} chunks.")
        print("The knowledge base is now updated with your internal documents.")
    else:
        print("\nIngestion completed with 0 documents indexed.")


if __name__ == "__main__":
    main()
