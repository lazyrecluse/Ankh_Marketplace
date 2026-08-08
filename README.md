# Ankh B2B Textile Marketplace

A B2B marketplace for textile suppliers and buyers: a **React SPA** frontend and a
**FastAPI** backend, wired together over HTTP/JSON with no shared build.

## Setup

### Backend

The schema is owned by Alembic, so migrate before the first start:

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

The app does not create tables on startup — running it against an unmigrated
database will fail on the first query. For a database that predates Alembic,
run `.venv/bin/alembic stamp 0001_baseline` once instead of upgrading.

Swagger UI is at http://localhost:8000/docs.

The virtualenv is managed by `uv` and has no `pip`. Install into it with:

```bash
cd backend && VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements.txt
```

### Frontend

```bash
npm install
npm start        # dev server on :3000
npm run build    # production bundle into build/
```

`REACT_APP_BACKEND_ENDPOINT` overrides the backend URL; it defaults to
`http://localhost:8000`.

## Tests

Run from the **repo root** — the suites import `backend.app.main`:

```bash
backend/.venv/bin/python -m pytest
```

`backend/tests/conftest.py` points `DATABASE_URL` at a throwaway SQLite file per
session, so tests never touch `backend/ankh_marketplace.db`.

There are no frontend tests; `npm test` runs the CRA/Jest harness against an
empty suite.

## Layout

```
src/                    React SPA
  Api/                  HTTP client + one module per feature area
  Auth/session.js       the only place that touches auth localStorage keys
  Components/  Pages/   UI
  Redux/                store concerns only (cart, categories, currencies)
backend/
  app/
    routers/            one module per OpenAPI tag
    models.py           SQLAlchemy models
    schemas.py          Pydantic request/response models
    security.py         password hashing, JWT, role dependencies
    serializers.py      product -> JSON shaping
    seed.py             startup seed (categories, currencies, demo catalog)
  alembic/              migrations
  tests/
```

## Configuration

Backend settings are read from the environment with the `ANKH_` prefix
(see `Settings` in `backend/app/security.py`):

| Variable | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///backend/ankh_marketplace.db` | Also how the Postgres in `docker-compose.yml` gets used |
| `ANKH_SECRET_KEY` | dev placeholder | Logs a warning if left at the default |
| `ANKH_ALLOWED_ORIGINS` | `["http://localhost:3000"]` | CORS allowlist |
| `ANKH_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime |

The demo supplier account seeded on first run is `supplier@ankh.com` / `password`.

`CLAUDE.md` documents the architecture, conventions, and known rough edges in
more detail.
