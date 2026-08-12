# TODO

## Wire AI assistant recommendations into catalog search

**Status:** blocked — see note below.

`POST /api/ai/chat` recommends fabrics in prose, but a shopper has no way to act
on the answer. When the assistant names products or describes what it is
suggesting, it should be able to hand off to the catalog filters that now exist.

The plumbing is already in place, so this is mostly a frontend job:

- `GET /api/products` accepts `search`, `category`, `climate`, `sensitive_skin`,
  `min_price`, `max_price`, `in_stock`, and `sort` (`backend/app/routers/products.py`).
- Catalog filter state lives in the URL and is built by
  `buildProductQuery()` in `src/Utils/productQuery.js`, so a "Show me these"
  button only needs to push `/products` + a query string.
- `src/Pages/Category/CategoryPage.js` refetches on any query-string change, so
  no new state wiring is required.

Sketch: have the chat endpoint return a structured `filters` object alongside the
prose reply, and render a button in `src/Components/AIAssistant/AIAssistant.js`
that calls `buildProductQuery()` with it and navigates.

**Blocker:** the local Qwen2.5-1.5B GGUF that `backend/app/ai_helper.py` loads
through `llama_cpp` destabilises the machine, so this cannot be exercised
end-to-end yet. Picking a lighter model, capping threads/context, or moving
inference behind a remote endpoint would unblock it. Note that `ai_helper.py`
silently falls back to a keyword scorer on any exception unless
`DEPLOYMENT_ENV`/`PRODUCTION`/`ENV` marks production — so a crashing model can
look like a working one from the API side.

**Since the Render deploy**, the endpoint is gated off by default:
`ai_helper.ai_enabled()` reads `ANKH_AI_ENABLED` (default false) and
`generate_ai_response` raises `AIDisabledError`, which the router turns into a
clean 503. `llama-cpp-python` moved out of `requirements.txt` into
`backend/requirements-ai.txt` so deploy builds never install it. To work on this
locally: `cd backend && VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements-ai.txt`
and set `ANKH_AI_ENABLED=true` in `backend/.env`.

## Uploaded images do not survive a deploy

Render's filesystem is ephemeral, and no persistent disk is attached (a
deliberate call — this is a personal project). `POST /api/upload` writes into
`backend/app/static/uploads/`, so every supplier-uploaded image disappears on the
next deploy or restart while the `Product.gallery` rows keep pointing at the dead
path, giving 404s.

Seeded products are unaffected — they were switched to absolute Unsplash URLs
during the deploy work, so a fresh database renders correctly.

The real fix is object storage (S3/Cloudinary): upload there and store absolute
URLs, which also removes the single-instance constraint a persistent disk imposes.

## Tests bypass migrations entirely

`backend/tests/conftest.py` builds its schema with `Base.metadata.create_all()`,
so the Alembic migrations are never exercised by the suite. A migration can be
completely broken while all 29 tests pass — which is exactly what happened:
`0002_json_rates_category` could not run on Postgres at all (it needed
`postgresql_using` on four `ALTER COLUMN ... TYPE JSON` statements) and nothing
caught it.

Worth a session-scoped fixture that runs `alembic upgrade head` against the
throwaway database instead, so schema drift and dialect breakage fail the build.

## Migration and seed race with more than one instance

The backend's start command runs `alembic upgrade head` before `uvicorn`, and the
startup hook seeds. With two or more instances booting concurrently, both would
race on the migration and on the seed's check-then-insert. Render's free tier is
single-instance so this is not a live problem, but it needs an advisory lock or a
one-off job before scaling out.

## Minor cleanups

- **`@app.on_event("startup")` is deprecated** (`backend/app/main.py`) in current
  FastAPI — migrate to a lifespan context manager. It emits a warning on every
  test run.
- **`.gitignore` has `.gguf`, not `*.gguf`** — that matches only a file literally
  named `.gguf`, so a real model file would not be ignored. Harmless while models
  live in `backend/app/ai_models/`, wrong the moment one lands elsewhere.
- **`POST /api/upload` has no size or content-type limit** and does
  `await file.read()` into memory, taking the file extension straight from the
  client-supplied filename (`backend/app/routers/products.py`).

