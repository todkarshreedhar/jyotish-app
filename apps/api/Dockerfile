
# Development image for the Jyotish API
FROM python:3.13

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

# Apply migrations and start the API server
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn jyotish_api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/apps/api/src --reload-dir /app/packages/engine/src"]
