"""Request handlers (framework glue omitted)."""
from __future__ import annotations

from datetime import datetime, timezone

from .store import SessionStore

STORE = SessionStore()


def login_handler(user_id: int) -> dict:
    session = STORE.create(user_id, datetime.now(timezone.utc))
    return {"token": session.token, "expires_at": session.expires_at.isoformat()}


def whoami_handler(token: str) -> dict:
    session = STORE.get(token, datetime.now(timezone.utc))
    if session is None:
        return {"status": 401}
    return {"status": 200, "user_id": session.user_id}


def logout_handler(token: str) -> dict:
    STORE.revoke(token)
    return {"status": 204}


def purge_job() -> int:
    """Run every 10 minutes by the scheduler."""
    return STORE.purge_expired(datetime.now(timezone.utc))
