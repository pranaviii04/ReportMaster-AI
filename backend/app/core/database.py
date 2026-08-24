from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


def _sqlite_file_path(url: str) -> Path | None:
    """Return the on-disk path for a SQLite URL, or None for :memory: / non-sqlite."""
    if not url.startswith("sqlite"):
        return None
    if ":memory:" in url:
        return None
    # sqlite:///./data/db.sqlite  -> ./data/db.sqlite
    # sqlite:////data/db.sqlite   -> /data/db.sqlite
    raw = url.replace("sqlite:///", "", 1)
    return Path(raw)


db_file = _sqlite_file_path(settings.DATABASE_URL)
if db_file is not None:
    db_file.parent.mkdir(parents=True, exist_ok=True)

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
