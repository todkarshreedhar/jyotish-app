# Deployment

The planned hosting (SDLC handbook) is Google Cloud in `asia-south1` (Mumbai): Cloud Run for the API and worker, Cloud SQL for PostgreSQL, Memorystore for Redis, and Vercel or Cloud Run for the web app. Infrastructure code (OpenTofu) is not written yet.

## Production settings

| Service | Command | Required settings |
|---|---|---|
| API | `sh -c "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn jyotish_api.main:app --host 0.0.0.0 --port 8000 --workers 2"` | `ENVIRONMENT=production`, `DATABASE_URL`, `REDIS_URL`, `WEB_URL`, `SECRET_KEY`, `DATA_ENCRYPTION_KEYS`, SMTP settings, optional Google and Sentry |
| Worker | `uv run --no-sync celery -A jyotish_api.worker worker --beat` | same as API |
| Web | `pnpm build && pnpm start` (or the standalone output) | `API_URL` pointing at the API |

The browser only talks to the web origin; Next.js forwards `/api/*` to the API, so cookies stay first-party.

Make a Fernet key with:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
