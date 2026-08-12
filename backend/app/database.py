import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchored to backend/ rather than the process CWD. Previously this was
# "sqlite:///./ankh_marketplace.db", which meant uvicorn started from backend/
# and pytest started from the repo root silently used two different databases.
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "ankh_marketplace.db"

_raw_url = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Render hands out DATABASE_URL using the legacy "postgres://" scheme, which
# SQLAlchemy 2.x rejects outright. Normalize it, and pin the driver explicitly
# so the default (psycopg2, which is not installed) is never selected.
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

SQLALCHEMY_DATABASE_URL = _raw_url

_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

# check_same_thread is a SQLite-only connect arg; passing it to any other
# driver raises. Keeping this conditional is what allows DATABASE_URL to point
# at the Postgres instance in docker-compose.yml.
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=_connect_args,
    # Managed Postgres drops idle connections (and Render's free tier spins the
    # service down), so without this the first request after a quiet period
    # fails on a stale pooled connection. No-op for SQLite.
    pool_pre_ping=not _is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
