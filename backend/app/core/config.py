"""
ReportMaster AI — Application Configuration
Loads all settings from the .env file using Pydantic v2 BaseSettings.
"""

import json
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Host dashboards usually pass a string. Accept:
    #   http://localhost:3000
    #   https://app.vercel.app,https://app-git-main.vercel.app
    #   ["https://app.vercel.app"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── JWT Authentication ───────────────────────────────────────────────────
    SECRET_KEY: str = "reportmaster_super_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        """Parse CORS origins from a list, JSON array, or comma-separated string."""
        if value is None or value == "":
            return ["http://localhost:3000"]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere else in the app
settings = Settings()
