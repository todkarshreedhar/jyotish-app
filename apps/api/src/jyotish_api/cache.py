"""Chart snapshot cache (US-25). Redis when available, in-process otherwise.

Keys are SHA-256 hashes of (inputs, settings, engine version), so the key
itself reveals nothing about the person.
"""

import hashlib
import json
import threading
from collections import OrderedDict
from typing import Any

import redis

from jyotish_api.settings import settings

TTL_SECONDS = 7 * 86400
_local: OrderedDict[str, str] = OrderedDict()
_lock = threading.Lock()
_client: redis.Redis | None = None


def _redis() -> redis.Redis | None:
    global _client
    if _client is None:
        try:
            c = redis.Redis.from_url(settings.redis_url, socket_timeout=0.5, socket_connect_timeout=0.5)
            c.ping()
            _client = c
        except Exception:
            return None
    return _client


def make_key(kind: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return f"jy:{kind}:" + hashlib.sha256(raw.encode()).hexdigest()


def get(key: str) -> str | None:
    r = _redis()
    if r is not None:
        try:
            v = r.get(key)
            return v.decode() if v else None
        except Exception:
            pass
    with _lock:
        v = _local.get(key)
        if v is not None:
            _local.move_to_end(key)
        return v


def put(key: str, value: str) -> None:
    r = _redis()
    if r is not None:
        try:
            r.setex(key, TTL_SECONDS, value)
            return
        except Exception:
            pass
    with _lock:
        _local[key] = value
        while len(_local) > 500:
            _local.popitem(last=False)


def incr_window(key: str, seconds: int) -> int:
    """Counter for rate limits; returns the new count in the window."""
    r = _redis()
    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.expire(key, seconds, nx=True)
            return int(pipe.execute()[0])
        except Exception:
            pass
    with _lock:
        n = int(_local.get(key, "0")) + 1
        _local[key] = str(n)
        return n
