# Image for the Jyotish API and its Celery worker.
# python:3.13 (not -slim) because pyswisseph needs a C compiler to build.
FROM python:3.13

# WeasyPrint (PDF reports) needs Pango; the fonts it uses are bundled in the app.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==0.11.*"

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# Copy dependency configuration first for Docker caching
COPY pyproject.toml uv.lock .python-version ./
COPY packages/engine/pyproject.toml packages/engine/README.md packages/engine/
COPY apps/api/pyproject.toml apps/api/README.md apps/api/

# Install dependencies before copying application code
RUN uv sync --frozen --no-install-workspace --package jyotish-api

# Copy the actual application source code
COPY packages/engine packages/engine
COPY apps/api apps/api

# Install the workspace packages
RUN uv sync --frozen --package jyotish-api

WORKDIR /app/apps/api

EXPOSE 8000

# Development default: apply migrations and start the API with reload.
# Production overrides the command (see infra/README.md).
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn jyotish_api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/apps/api/src --reload-dir /app/packages/engine/src"]
