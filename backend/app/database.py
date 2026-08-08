import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchored to backend/ rather than the process CWD. Previously this was
# "sqlite:///./ankh_marketplace.db", which meant uvicorn started from backend/
# and pytest started from the repo root silently used two different databases.
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "ankh_marketplace.db"

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# check_same_thread is a SQLite-only connect arg; passing it to any other
# driver raises. Keeping this conditional is what allows DATABASE_URL to point
# at the Postgres instance in docker-compose.yml.
_connect_args = (
    {"check_same_thread": False}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
