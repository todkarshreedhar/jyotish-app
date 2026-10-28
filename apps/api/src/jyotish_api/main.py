import logging
import threading
import time
import uuid
from typing import Any

import redis
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from jyotish_engine import engine_info
from jyotish_engine.names import LANGS, names

from jyotish_api.crypto import check_production_secrets
from jyotish_api.db import database_is_up
from jyotish_api.routers import admin, alerts, auth, developer, me, profiles, reports, tools
from jyotish_api.settings import settings

log = logging.getLogger("jyotish_api")

check_production_secrets()

if settings.sentry_dsn:
    import sentry_sdk

    def _scrub(event: Any, hint: Any) -> Any:
        # Never send request bodies, cookies or query strings: they can hold birth data (US-06).
        req = event.get("request") or {}
        for k in ("data", "cookies", "query_string", "headers"):
            req.pop(k, None)
        event.pop("user", None)
        return event

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.app_version,
        send_default_pii=False,
        before_send=_scrub,
        traces_sample_rate=0.05,
    )

app = FastAPI(
    title="Jyotish API",
    version=engine_info()["engine_version"],
    description="Vedic astrology calculations (sidereal, Swiss Ephemeris). Open source under AGPL-3.0.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF", "X-API-Key"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next: Any) -> Response:
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    start = time.perf_counter()
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    for k, v in getattr(request.state, "extra_headers", {}).items():
        response.headers[k] = v
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith(("/v1/", "/public/")):
        response.headers.setdefault("Cache-Control", "no-store")
    # Log path and timing only: never query strings or bodies (they can hold birth data).
    log.info(
        "%s %s %s %.0fms rid=%s",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - start) * 1000,
        rid,
    )
    return response


for r in (
    auth.router,
    me.router,
    profiles.router,
    tools.router,
    reports.router,
    admin.router,
    alerts.router,
    developer.router,
    developer.public,
):
    app.include_router(r)


def redis_is_up() -> bool:
    try:
        return bool(redis.Redis.from_url(settings.redis_url, socket_timeout=1).ping())
    except Exception:
        return False


@app.get("/health")
def health() -> dict:
    """Tells the web app (and later, Cloud Run) that every part is working."""
    db_ok = database_is_up()
    redis_ok = redis_is_up()
    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "database": "up" if db_ok else "down",
        "redis": "up" if redis_ok else "down",
        "version": settings.app_version,
        **engine_info(),
    }


@app.get("/v1/names")
def get_names(lang: str = "en") -> dict[str, Any]:
    """Planet, sign, Nakshatra and Panchang names in the requested language."""
    return {"lang": lang if lang in LANGS else "en", **names(lang)}


@app.on_event("startup")
def _seed_places() -> None:
    if settings.environment == "test":
        return

    def run() -> None:
        try:
            from jyotish_api.db import SessionLocal
            from jyotish_api.services.places import seed

            with SessionLocal() as db:
                n = seed(db)
                if n:
                    log.info("loaded %d places", n)
        except Exception:
            log.exception("place seeding failed (search will be empty until it succeeds)")

    threading.Thread(target=run, daemon=True).start()
