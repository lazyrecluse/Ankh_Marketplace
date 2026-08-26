# Backend image: FastAPI + uvicorn.
#
# Build context is backend/ (see dockerContext in render.yaml), so paths here are
# relative to that directory, not the repo root.

FROM python:3.12-slim

# Bytecode is pointless in a container that is rebuilt on every deploy, and
# unbuffered stdout means logs reach Render's log stream immediately rather than
# sitting in a pipe buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copied on its own so this layer is cached and pip only re-runs when the
# dependency list actually changes, not on every source edit.
#
# No build-essential: psycopg[binary] ships a prebuilt libpq wheel, and
# llama-cpp-python (the one dependency that would need a compiler) lives in
# requirements-ai.txt and is deliberately not installed here.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Fallback location for a SQLite file when DATABASE_URL is unset or points here.
# The deployed blueprint uses managed Postgres instead (free web services cannot
# attach a persistent disk, and the container filesystem is ephemeral), so on
# Render this directory stays empty. Kept so `docker run` without a DATABASE_URL
# still works locally.
RUN mkdir -p /app/db_data

# Documents the local default. Render ignores this and routes to $PORT.
EXPOSE 8000

# Migrations run at start, not build: the build has no access to the mounted
# disk or a managed database. The `&&` is load-bearing — no app code calls
# create_all(), so booting against an unmigrated database crashes
# seed_db_if_empty() on its first query.
#
# $PORT is what Render binds; the fallback keeps `docker run` working locally.
# Shell form (not exec) so the variable is actually expanded.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
