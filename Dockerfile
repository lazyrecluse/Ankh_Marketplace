# Frontend image: build the CRA bundle, then serve it with nginx.
#
# Two stages so the runtime image carries only static files and nginx — no Node,
# no node_modules, no source. That is ~40MB instead of ~1.5GB.

# ------------------------------------------------------------------ deps stage
# Split from the build so `docker compose --target deps` (used for local dev)
# gets node_modules and the dev server without inheriting the production-only
# CI=true below, which would turn lint warnings into hard errors in `npm start`.
FROM node:22-alpine AS deps

WORKDIR /app

# Cached unless the lockfile changes. `npm ci` (not install) so the build uses
# exactly the locked versions — sass in particular resolves to a release
# requiring Node >=20.19 under the ^1.71.1 range.
COPY package.json package-lock.json ./
RUN npm ci

# ----------------------------------------------------------------- build stage
FROM deps AS build

COPY . .

# CRA inlines REACT_APP_* into the bundle at BUILD time, so this must arrive as a
# build arg — a value set only at container start would never reach the compiled
# JavaScript. Render passes a Docker service's env vars through as --build-args,
# which is how render.yaml supplies it. Changing it needs a rebuild, not a
# restart.
#
# No default on purpose: back_end_endpoint() then falls back to
# http://localhost:8000, which is right for local dev and wrong for a deploy, so
# render.yaml must set it explicitly.
ARG REACT_APP_BACKEND_ENDPOINT
ENV REACT_APP_BACKEND_ENDPOINT=$REACT_APP_BACKEND_ENDPOINT

# Warnings-as-errors, deliberately: a lint warning that is merely noisy locally
# should fail the image build rather than ship. .github/workflows/ci.yml applies
# the same rule. Scoped to this stage so the dev server is unaffected.
ENV CI=true
RUN npm run build

# -------------------------------------------------------------- runtime stage
FROM nginx:1.27-alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

# The nginx:alpine entrypoint envsubst's /etc/nginx/templates/*.template into
# /etc/nginx/conf.d/ at startup, which is how $PORT from Render reaches the
# listen directive. The FILTER is load-bearing: without it envsubst would also
# replace nginx's own $uri/$host with empty strings and produce a broken config.
ENV PORT=8080 \
    NGINX_ENVSUBST_FILTER=PORT

EXPOSE 8080

