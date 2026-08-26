# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo shape

Two apps in one repo: a Create React App SPA at the root (`src/`, `public/`) and a FastAPI backend under `backend/`. They are wired only over HTTP/JSON — no shared build.

## Commands

Frontend (repo root):

```bash
npm start                 # dev server on :3000
npm run build             # production bundle into build/
npm test                  # react-scripts/Jest — no test files exist yet
```

Backend — run from `backend/`. The schema is owned by Alembic, so migrate before the first start:

```bash
cd backend && .venv/bin/alembic upgrade head
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
```

The app no longer calls `Base.metadata.create_all()`; starting it against an unmigrated database will fail on the first query. For a database that predates Alembic, run `.venv/bin/alembic stamp 0001_baseline` once instead of upgrading.

`app/database.py` resolves the SQLite file to `backend/ankh_marketplace.db` regardless of the working directory, and honours a `DATABASE_URL` override. That override is how the test suite and the `docker-compose.yml` Postgres are pointed elsewhere.

Swagger UI is at `http://localhost:8000/docs`, OpenAPI JSON at `/openapi.json` (both verified working).

Pytest must run from the **repo root**, since the suites import `backend.app.main`. The root `pytest.ini` sets `pythonpath = .` so that works with a plain `pytest` invocation:

```bash
backend/.venv/bin/python -m pytest                                 # all (29 passing)
backend/.venv/bin/python -m pytest backend/tests/test_e2e_suite.py # one file
backend/.venv/bin/python -m pytest backend/tests/test_e2e_suite.py::test_r1_image_upload_valid_file
```

`backend/tests/conftest.py` points `DATABASE_URL` at a throwaway SQLite file per session and seeds it explicitly, so tests never touch `backend/ankh_marketplace.db`. It also exposes `client`, `make_user`, `buyer`, and `supplier` fixtures — prefer those over the older `time.time_ns()` unique-email pattern in new tests.

The venv is managed by `uv` and has no `pip`. Install into it with:

```bash
cd backend && VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements.txt
```

`backend/docker-compose.yml` provisions Postgres that nothing connects to by default; it becomes usable via `DATABASE_URL`.

## Deployment

`render.yaml` at the repo root is a Render blueprint defining two **Docker** services: the FastAPI backend (`ankh-api`) and the CRA frontend (`ankh-web`). Both use `runtime: docker` and build from a Dockerfile — `backend/Dockerfile` (context `backend/`) and the root `Dockerfile` (context `.`). The backend persists a SQLite file on a mounted disk (`/app/db_data`); there is no managed-Postgres service in the current blueprint. `.github/workflows/ci.yml` runs the pytest suite and a `CI=true` frontend build on push and PR — independent of Render's auto-deploy.

`docker-compose.yml` at the repo root is **local development only** — Render never reads it. It runs Postgres + the backend (uvicorn `--reload`) + the frontend (CRA dev server), so `docker compose up --build` reproduces the deployed stack. The frontend service builds only the Dockerfile's `deps` stage and bind-mounts `src/`/`public/` for hot reload; Render builds the whole Dockerfile and gets nginx.

Things that differ from local and are easy to get wrong:

- **The frontend Dockerfile is multi-stage:** `deps` (npm ci) → `build` (npm run build, with `CI=true` and `ARG REACT_APP_BACKEND_ENDPOINT`) → an `nginx:alpine` runtime serving the static bundle. `nginx.conf` is a template — the nginx entrypoint runs `envsubst` on `${PORT}` at startup, guarded by `NGINX_ENVSUBST_FILTER=PORT` so nginx's own `$uri`/`$host` are not blanked out. The SPA rewrite (`try_files $uri $uri/ /index.html`) lives here, not in Render config, so a hard refresh on `/products/:id` does not 404.
- **`REACT_APP_BACKEND_ENDPOINT` reaches the build as a Docker `--build-arg`.** Render automatically passes a Docker service's env vars to the image build as build args, which is how the `envVars` entry feeds the Dockerfile's `ARG`. CRA inlines `REACT_APP_*` at **build** time, so changing it needs a **rebuild**, not a restart. It is the only `REACT_APP_*` variable in the codebase.
- **Migrations run in the container CMD**, not the build: `alembic upgrade head && uvicorn ...`. The build has no access to the mounted disk. The `&&` is load-bearing — nothing calls `create_all()` in app code, so booting against an unmigrated database crashes `seed_db_if_empty()` on its first query. The CMD binds `${PORT:-8000}` so Render's injected `$PORT` wins and `docker run` still works locally.
- **`DATABASE_URL` is normalised in `app/database.py`.** The current blueprint uses SQLite on a disk (`sqlite:////app/db_data/...` — four slashes). To switch to managed Postgres instead, add a `databases:` block and point `DATABASE_URL` at it with `fromDatabase`: the code already rewrites Render's `postgres://` to `postgresql+psycopg://`, `pool_pre_ping` is on for non-SQLite, and psycopg 3 is in `requirements.txt`.
- **`ANKH_ALLOWED_ORIGINS` must be the exact frontend origin.** `main.py` sets `allow_credentials=True`, which makes a `*` wildcard illegal under the CORS spec. (Two separate origins means CORS is real here — the split-service Docker setup does not remove it.)
- **`ANKH_SECRET_KEY` must be set** when `DEPLOYMENT_ENV=production`, or `app/security.py` raises at import and the service refuses to boot rather than signing JWTs with a per-process key. `render.yaml` uses `generateValue: true`.
- **`ANKH_AI_ENABLED` defaults to false**, and `llama-cpp-python` lives in `backend/requirements-ai.txt` rather than `requirements.txt`, so the deploy image never installs it. `POST /api/ai/chat` returns 503 while disabled.
- **`.dockerignore` at both contexts is load-bearing for image size:** the root one excludes `node_modules`, `backend/`, and secrets from the frontend build; `backend/.dockerignore` excludes `.venv`, `*.db`, `app/ai_models` (the ~1.1 GB GGUF), and `app/static/uploads`.

Migration `0002` carries `postgresql_using="<col>::json"` on its four `ALTER COLUMN ... TYPE JSON` statements. Postgres refuses that cast from `text` without an explicit `USING`, even on empty tables; SQLite ignores the kwarg because batch mode rebuilds the table instead. Verify any future type-change migration against both dialects — `DATABASE_URL='postgres://u:p@h/db' alembic upgrade head --sql` renders the Postgres DDL without needing a live server.

## Architecture

### The legacy-shape contract

The React app started as a Scandiweb GraphQL store; the FastAPI backend was retrofitted to emit the JSON shape those components already expected. Several oddities follow from that and should be preserved unless deliberately migrating:

- `build_product_prices()` in `main.py` fabricates USD/EUR/GBP entries from the single stored `price_amount` at fixed rates (0.92, 0.79). The DB holds one price per product.
- `attributes` is a hardcoded Size S/M/L block injected by the product endpoints so `ProductCard`, `DescriptionPage`, and the cart-matching logic keep working.
- Currency switching is entirely client-side: `CurrentCurrency` is an index into `AllCurrencies`, and components select by `prices[].currency.symbol`.
- `src/GraphQL/Queries.js` and `src/Configs/GraphQLClient.js` are dead code; every call goes through `fetch` plus `back_end_endpoint()`.

### Backend (`backend/app/`)

- `main.py` holds all ~24 routes, tagged Auth / Onboarding / Products / Orders / Supplier / AI Assistant for Swagger grouping. `models.py`, `schemas.py`, `auth.py`, `seed.py`, `ai_helper.py` are the supporting modules.
- `Product.id` is a **string slug primary key**. `POST /api/supplier/products` slugifies `name + brand` and appends a short uuid hash on collision; the frontend no longer sends an id.
- `gallery` and `recommended_climate` are JSON strings in TEXT columns, as are `BuyerProfile.skin_preferences` and `SupplierProfile.categories`. Every read/write does `json.loads`/`json.dumps` at the boundary — easy to miss when adding a field.
- Authorization is an inline `current_user.role != "supplier"` check plus a 403 in each handler, not a shared dependency.
- `auth.py` hand-rolls `pbkdf2_hmac` password hashing (passlib is installed but unused) and JWT HS256 with a hardcoded `SECRET_KEY` and 24h expiry.
- `GET /api/products` filters `category` with a SQL `id LIKE '<cat>%' OR name LIKE '%<cat>%'`, then applies `climate` and `sensitive_skin` in Python after the query returns.
- `POST /api/upload` returns `{url, image_url}` pointing at `/static/uploads/<uuid><ext>`, mounted from `backend/app/static/uploads` (gitignored apart from `.gitkeep`).
- `seed_db_if_empty()` runs on startup: categories, currencies, the demo supplier `supplier@ankh.com` / `password`, and the fabric catalog. It also copies jpgs from a machine-specific `/home/ankabut/images` when that directory exists.
- `POST /api/ai/chat` runs a local Qwen2.5-1.5B GGUF through `llama_cpp` (`backend/app/ai_models/`, ~1.1 GB, auto-downloaded on first use). On any exception it silently falls back to a keyword scorer unless `DEPLOYMENT_ENV`/`PRODUCTION`/`ENV` marks production.
- CORS is `allow_origins=["*"]`.

### Frontend (`src/`)

- Mixed component styles: older store pages (`App`, `AppBar`, `CategoryPage`, `DescriptionPage`, `CartPage`, `ProductCard`) are class components wired with `connect()`; everything added for the marketplace (`AuthPage`, both Onboarding pages, both Dashboards, `AIAssistant`) is function components with hooks and local state.
- **react-router-dom v5** — `Switch`, `useHistory`, `withRouter`. Not v6.
- Redux (`src/Redux/`) holds only store concerns: categories, currencies, cart, product list. It is persisted to localStorage via redux-persist under key `scandiweb-store`. Auth state deliberately lives outside Redux, in `localStorage` under `token`, `role`, and `user` — components read those keys directly, and logout clears storage, dispatches `RESET_STORE`, then hard-navigates.
- Every backend call is `fetch(back_end_endpoint() + path)`; `back_end_endpoint()` reads `REACT_APP_BACKEND_ENDPOINT` and defaults to `http://localhost:8000`. No API client layer.
- Gallery URLs are relative when uploaded and absolute when seeded from Unsplash, so consumers do `url.startsWith('/') ? back_end_endpoint() + url : url`. Repeat that guard when rendering images anywhere new.
- The AppBar is `position: fixed` at 80px tall and is suppressed on `/login*` by a path check in `App.js`. Full-page containers must clear it — `.dashboard-container` uses `padding: 100px 30px 40px`, and `backend/tests/test_e2e_suite.py` asserts `padding-top >= 100px` on `.auth-container`, `.onboard-container`, and `.dashboard-container` by parsing the SCSS. `.auth-container` and `.onboard-container` currently satisfy this via `min-height: 80vh` centering rather than an explicit `padding-top`.
- SCSS lives next to each component; `src/Utils/Colors.scss` and `src/Fonts/Fonts.scss` are imported once in `index.js`.

### Routes

`/products` (catalog, with category tiles on "all") · `/products/:id` · `/carts` · `/checkout` · `/login` and `/login/buyer` (same `AuthPage` with `buyerMode`) · `/onboarding/buyer` · `/onboarding/supplier` · `/buyer/dashboard` · `/supplier/dashboard`. `/` redirects to `/products`.

Post-login routing branches on role and on whether onboarding is complete — buyers are sent to `/onboarding/buyer` until `profile.business_type` is set, suppliers to `/onboarding/supplier` until `profile.business_name` is set.

## Tests

`backend/tests/` contains the whole suite; there are no frontend tests. `test_e2e_suite.py` (25 cases) is organized in tiers — feature coverage, boundary cases, cross-feature flows, then full multi-actor lifecycle — and mixes API tests with SCSS/`App.js` source assertions for the layout requirements. `test_integration.py` covers auth, onboarding, and supplier flows; `test_ai_assistant.py` mocks out `generate_ai_response` so the LLM never loads.

Tests share one `TestClient(app)` and the on-disk SQLite file with no fixtures or teardown, so isolation comes from unique emails built with `time.time_ns()`. Follow that pattern rather than assuming a clean database. `TEST_INFRA.md` and `TEST_READY.md` document the suite in detail.

## Working docs

`PROJECT.md`, `ORIGINAL_REQUEST.md`, `TEST_INFRA.md`, `TEST_READY.md`, and `.agents/` are gitignored scratch state from previous agent runs — useful as history, not authoritative about current code. `README.md` is the untouched Create React App boilerplate. Note that `.gitignore` also excludes `*.db` and `backend/app/static/uploads/`, so seeded images and the database are local-only.
