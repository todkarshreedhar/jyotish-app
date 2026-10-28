# Deployment

The planned hosting (SDLC handbook) is Google Cloud in `asia-south1` (Mumbai): Cloud Run for the API and worker, Cloud SQL for PostgreSQL, Memorystore for Redis, and Vercel or Cloud Run for the web app. The infrastructure is written as OpenTofu code in [`infra/tofu`](tofu/).

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

## Setting up Google Cloud with OpenTofu

You need a Google Cloud project with billing turned on, `gcloud` and OpenTofu 1.8 or newer.

1. Make a bucket for the OpenTofu state (once per project):

   ```bash
   gcloud storage buckets create gs://$PROJECT-tofu-state --location asia-south1 --uniform-bucket-level-access
   gcloud storage buckets update gs://$PROJECT-tofu-state --versioning
   ```

2. Build and push the images to Artifact Registry (`apps/api/Dockerfile`, `apps/web/Dockerfile`).

3. Copy `tofu/production.tfvars.example` to `production.tfvars` and fill it in. Then:

   ```bash
   cd infra/tofu
   tofu init -backend-config="bucket=$PROJECT-tofu-state" -backend-config="prefix=production"
   tofu apply -var-file=production.tfvars
   ```

   The first apply makes the network, Cloud SQL (Postgres 17, daily backups, point-in-time recovery, high availability in production), Redis, the secrets, the three Cloud Run services, the migration job, uptime checks and alerts.

4. Add the secret values (never put them in code or tfvars):

   ```bash
   printf %s "$VALUE" | gcloud secrets versions add jyotish-production-secret-key --data-file=-
   ```

   Do this for `secret-key`, `data-encryption-keys`, `smtp-password`, `google-client-secret` and `sentry-dsn`. The database URL secret is filled in by OpenTofu.

5. Run the migrations (the API loads the city list on its first start):

   ```bash
   gcloud run jobs execute jyotish-production-migrate --region asia-south1 --wait
   ```

6. Point the domain at the web service (`gcloud run domain-mappings create` or a load balancer), and confirm the alert email address the first time Google sends a verification.

For each later release: push new images, set `api_image` and `web_image`, run `tofu apply`, then run the migration job.

## Checks before launch

- Backup restore test: [runbooks/restore-test.md](runbooks/restore-test.md).
- Load test: the `Load test` GitHub workflow (k6, 50 requests a second for 2 minutes, fails if p95 is over 300 ms). Run it against staging from the Actions tab. `tools/load/quick_load.py` does a smaller check without k6.
- Security: CI runs `pip-audit`, `bandit`, `pnpm audit` and an OWASP ZAP baseline scan on every pull request.
- `IP_RATE_LIMITS=false` is only for local load tests. The API refuses to start with it in production.
