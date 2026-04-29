"""
ReportMaster AI — PDF Upload Router
Allows users to upload accounting manuals directly through the UI.
"""

import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import settings
from app.models.schemas import IngestResponse
from app.routers.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingestion"])

@router.post("/upload", response_model=IngestResponse)
async def upload_manual(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """
    Upload a PDF file, save it to the manuals directory, and trigger re-indexing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # 1. Save file to disk
    manuals_dir = Path(settings.MANUALS_DIR)
    manuals_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = manuals_dir / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info("File saved to %s", file_path)
    except Exception as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(exc)}")

    # 2. Trigger Ingestion
    # For now, we'll just return success and tell the user to wait a moment.
    # In a real app, we'd run this in a background task.
    # I'll implement a simple blocking ingestion call for now to keep it simple.
    from scripts.ingest_manuals import run_ingestion
    
    try:
        count = run_ingestion()
        return IngestResponse(
            message=f"Successfully uploaded and indexed '{file.filename}'.",
            documents_indexed=count
        )
    except Exception as exc:
        logger.error("Ingestion failed after upload: %s", exc)
        raise HTTPException(status_code=500, detail=f"File uploaded but indexing failed: {str(exc)}")
