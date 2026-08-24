"""
ReportMaster AI — Application Configuration
Loads all settings from the .env file using Pydantic v2 BaseSettings.
"""

import json
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(value: object) -> list[str]:
    """Parse *, a single origin, comma-separated origins, or a JSON array."""
    if value is None or value == "":
        return ["http://localhost:3000"]
    if isinstance(value, list):
        return [str(origin).strip() for origin in value if str(origin).strip()]
    stripped = str(value).strip()
    if stripped.startswith("["):
        parsed = json.loads(stripped)
        return [str(origin).strip() for origin in parsed if str(origin).strip()]
    return [origin.strip() for origin in stripped.split(",") if origin.strip()]


def get_cors_origin_list() -> list[str]:
    """
    Read CORS_ORIGINS from the process environment, not from BaseSettings.

    pydantic-settings JSON-decodes complex / list-like fields before validators
    run. Railway values such as * or http://localhost:3000 are not JSON and
    crash Settings() at import time, so this variable is kept off the model.
    """
    return _parse_cors_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))


class Settings(BaseSettings):
    """Central configuration object populated from environment variables / .env file."""

    # ── LLM / Google Gemini ──────────────────────────────────────────────────
    GOOGLE_API_KEY: str = "your_google_key_here"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    COLLECTION_NAME: str = "financial_manuals"

    # ── Embeddings ───────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Retrieval ────────────────────────────────────────────────────────────
    TOP_K_RESULTS: int = 5

    # ── Document Chunking ────────────────────────────────────────────────────
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # ── RAG — Data Sources ───────────────────────────────────────────────────
    # Local directory where internal PDF manuals are stored
    MANUALS_DIR: str = str(Path(__file__).parent.parent.parent / "data" / "manuals")

    # ── SQLite (users) ───────────────────────────────────────────────────────
    # Relative path keeps local dev unchanged. On Railway set:
    # DATABASE_URL=sqlite:////data/reportmaster.db
    DATABASE_URL: str = "sqlite:///./data/reportmaster.db"

    # ── JWT Authentication ───────────────────────────────────────────────────
    SECRET_KEY: str = "reportmaster_super_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere else in the app
settings = Settings()
