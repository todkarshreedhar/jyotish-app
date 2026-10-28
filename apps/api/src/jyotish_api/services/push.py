"""Push messages to the mobile app through Expo's push service (US-85).

Expo forwards each message to Firebase (Android) or APNs (iOS). We only
send short alert text, never birth details.
"""

import logging
import re
from typing import Any

import httpx

from jyotish_api.settings import settings

log = logging.getLogger(__name__)
outbox: list[dict[str, Any]] = []  # filled in tests

TOKEN_RE = re.compile(r"^Expo(nent)?PushToken\[[A-Za-z0-9_\-]{10,100}\]$")


def valid_token(token: str) -> bool:
    return bool(TOKEN_RE.match(token))


def send(tokens: list[str], title: str, body: str, data: dict[str, Any] | None = None) -> list[str]:
    """Send one message to each token. Returns the tokens Expo says are dead
    (the app was removed), so the caller can delete them."""
    messages: list[dict[str, Any]] = [
        {"to": t, "title": title, "body": body, "data": data or {}, "sound": "default"} for t in tokens
    ]
    if not messages:
        return []
    if settings.environment == "test":
        outbox.extend(messages)
        return []
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if settings.expo_access_token:
        headers["Authorization"] = f"Bearer {settings.expo_access_token}"
    dead: list[str] = []
    for i in range(0, len(messages), 100):  # Expo takes at most 100 per request
        chunk = messages[i : i + 100]
        try:
            r = httpx.post(settings.expo_push_url, json=chunk, headers=headers, timeout=15)
            r.raise_for_status()
            tickets = r.json().get("data", [])
        except Exception:
            log.exception("push delivery failed")
            continue
        for msg, ticket in zip(chunk, tickets, strict=False):
            if ticket.get("status") == "error" and (ticket.get("details") or {}).get("error") == "DeviceNotRegistered":
                dead.append(msg["to"])
    return dead
