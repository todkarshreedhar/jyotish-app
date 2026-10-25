# ADR 0001: Use a Monorepo

- **Status:** Accepted
- **Date:** 2026-10-25

## Context

A small team is building three related parts of the Jyotish App: a web application, a backend API, and an astrology calculation engine. These parts change together and need to be developed, tested, and maintained as one product.

Keeping the code in separate repositories would make coordinated changes harder to review and maintain.

## Decision

We will keep all three parts in one Git repository.

- The **Python API** will live in `apps/api/`.
- The **astrology engine** will live in `packages/engine/`.
- The **web application** will live in `apps/web/`.

The Python API and astrology engine will share a `uv` workspace and lockfile. The web application will remain an independent `pnpm` project with its own dependencies and lockfile.

Docker Compose will provide a consistent local development environment for the web app, API, PostgreSQL, and Redis.

## Consequences

### Positive

- A single pull request can update the API, astrology engine, and the screen that uses them.
- Shared changes can be reviewed together.
- Local development is standardized through Docker Compose.
- Python dependencies are managed centrally, while the frontend retains its own package management.

### Trade-offs

- The repository contains multiple technologies and requires clear folder boundaries.
- CI must run only the relevant checks for changed folders instead of running every check for every change.

The selective CI behavior is tracked as **US-02**.
