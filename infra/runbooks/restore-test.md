# Runbook: backup restore test (US-57)

Do this once before launch and then every quarter. A backup only counts once it has been restored.

Cloud SQL keeps 30 daily backups (taken at 02:00 IST) and 7 days of write-ahead logs, so any moment in the last 7 days can be restored.

## 1. Make a copy at a point in time

Pick a time from the last hour (UTC, RFC 3339):

```bash
ENV=production
SRC=jyotish-$ENV
COPY=$SRC-restore-$(date +%Y%m%d)
gcloud sql instances clone $SRC $COPY \
  --point-in-time "2026-11-01T10:00:00Z" --project $PROJECT
```

This makes a separate instance. The live database is not touched. It takes 10 to 30 minutes.

## 2. Check the copy

```bash
gcloud sql connect $COPY --user jyotish --database jyotish --project $PROJECT
```

Then run:

```sql
SELECT version_num FROM alembic_version;      -- matches the live database
SELECT count(*) FROM users;                    -- close to the live count
SELECT count(*) FROM profiles;
SELECT max(created_at) FROM profiles;          -- just before the chosen time
```

Decrypt one profile to prove the encryption keys still work with the restored data. From an API container, with `DATABASE_URL` pointing at the copy:

```bash
uv run --no-sync python -c "
from jyotish_api.crypto import decrypt_json
from jyotish_api.db import SessionLocal
from jyotish_api.models import Profile
with SessionLocal() as db:
    p = db.query(Profile).first()
    print(p.id, sorted(decrypt_json(p.birth_enc)))
"
```

## 3. Record and clean up

Write the date, the chosen time, how long the clone took and the row counts in the release notes or the ops log. Then delete the copy (it costs money while it runs):

```bash
gcloud sql instances delete $COPY --project $PROJECT
```

## If the live database is lost

1. Make a copy as in step 1, at the last good time.
2. Point the `jyotish-$ENV-database-url` secret at the copy's private IP (`gcloud secrets versions add`).
3. Redeploy the API, worker and migration job so they read the new secret.
4. Once stable, import the copy into OpenTofu state, or rebuild from it with `tofu apply`.

Target: back online within 4 hours, at most 5 minutes of data lost.
