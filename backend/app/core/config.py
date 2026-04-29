"""
ReportMaster AI — Application Configuration
Loads all settings from the .env file using Pydantic v2 BaseSettings.
"""

from pathlib import Path
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

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    # ── JWT Authentication ───────────────────────────────────────────────────
    SECRET_KEY: str = "reportmaster_super_secret_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    model_config = SettingsConfigDict(

        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere else in the app
settings = Settings()
