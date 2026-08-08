"""Shared pytest fixtures for the backend suite.

Two things happen here that the rest of the suite depends on:

1. ``DATABASE_URL`` is set at *import* time, before any test module runs.
   ``backend.app.database`` reads that variable when it is imported, and the
   existing test modules import the app at module level, so setting it inside a
   fixture would be too late. Every run therefore gets a throwaway SQLite file
   instead of scribbling on the developer's ``backend/ankh_marketplace.db``.

2. The schema is created and seeded explicitly. The older test modules build
   their own ``TestClient(app)`` at module scope without the context-manager
   form, which means Starlette never runs the lifespan/startup hook and the
   seed would otherwise never happen.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# --- must run before backend.app.* is imported anywhere ---------------------
_TMP_DIR = tempfile.mkdtemp(prefix="ankh-tests-")
_TEST_DB_PATH = Path(_TMP_DIR) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    """Create and seed the throwaway database once per test session."""
    from backend.app import models  # noqa: F401  (registers the mappers)
    from backend.app.database import Base, SessionLocal, engine
    from backend.app.seed import seed_db_if_empty

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_db_if_empty(db)
    finally:
        db.close()

    yield

    engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


@pytest.fixture(scope="session")
def client():
    """A TestClient bound to the app, with lifespan events run.

    Session-scoped: entering the context manager runs the startup hook, which
    re-runs the (idempotent) seed. Doing that per-test would be pure overhead.
    """
    from fastapi.testclient import TestClient

    from backend.app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def make_user(client):
    """Register + log in a fresh user, returning its token and auth headers.

    Replaces the ``time.time_ns()`` email trick that the older modules use to
    fake isolation. Those still work unchanged; new tests should prefer this.
    """

    def _make(role: str = "buyer", password: str = "password123") -> dict:
        email = f"{role}-{uuid.uuid4().hex[:12]}@ankh.test"

        registered = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "role": role},
        )
        assert registered.status_code == 201, registered.text

        logged_in = client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert logged_in.status_code == 200, logged_in.text

        token = logged_in.json()["access_token"]
        return {
            "email": email,
            "password": password,
            "role": role,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    return _make


@pytest.fixture
def buyer(make_user):
    return make_user("buyer")


@pytest.fixture
def supplier(make_user):
    return make_user("supplier")
