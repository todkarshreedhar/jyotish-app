import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jyotish_engine import engine_info

from jyotish_api.db import database_is_up
from jyotish_api.settings import settings

app = FastAPI(title="Jyotish API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        **engine_info(),
    }