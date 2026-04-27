"""
ReportMaster AI — Application Configuration
Loads all settings from the .env file using Pydantic v2 BaseSettings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object populated from environment variables / .env file."""

    # ── LLM / OpenAI ────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = "your_openai_key_here"

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

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere else in the app
settings = Settings()
