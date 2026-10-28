"""Encryption of birth data at rest (US-17, NFR-05) and token hashing."""

import hashlib
import hmac
import json
import secrets
from typing import Any

from cryptography.fernet import Fernet, MultiFernet

from jyotish_api.settings import settings

_DEV_KEY = "ZGV2LW9ubHkta2V5LWNoYW5nZS1tZS0zMi1ieXRlcyE="


def _fernet() -> MultiFernet:
    keys = [k.strip() for k in settings.data_encryption_keys.split(",") if k.strip()]
    return MultiFernet([Fernet(k) for k in keys])


def encrypt_json(data: dict[str, Any]) -> bytes:
    return _fernet().encrypt(json.dumps(data, sort_keys=True, ensure_ascii=False).encode())


def decrypt_json(blob: bytes) -> dict[str, Any]:
    return json.loads(_fernet().decrypt(bytes(blob)))


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def token_hash(token: str) -> str:
    """Keyed hash so a database leak does not reveal usable tokens."""
    return hmac.new(settings.secret_key.encode(), token.encode(), hashlib.sha256).hexdigest()


def check_production_secrets() -> None:
    if settings.is_production:
        if "dev-only" in settings.secret_key or len(settings.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must be set to a strong value in production")
        if _DEV_KEY in settings.data_encryption_keys:
            raise RuntimeError("DATA_ENCRYPTION_KEYS must be set in production")
        if not settings.ip_rate_limits:
            raise RuntimeError("IP_RATE_LIMITS cannot be turned off in production")
