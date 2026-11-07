"""In-process session store (one per worker; sessions are sticky to a worker)."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from .models import Session


class SessionStore:
    def __init__(self, ttl: timedelta = timedelta(hours=12)) -> None:
        self.ttl = ttl
        self._items: list[Session] = []          # creation order, used by purge and admin listing
        self._by_token: dict[str, Session] = {}

    def create(self, user_id: int, now: datetime) -> Session:
        session = Session(secrets.token_urlsafe(32), user_id, now + self.ttl)
        self._items.append(session)
        self._by_token[session.token] = session
        return session

    def get(self, token: str, now: datetime) -> Session | None:
        session = self._by_token.get(token)
        if session is None or not session.is_valid(now):
            return None
        return session

    def active_for_user(self, user_id: int, now: datetime) -> list[Session]:
        return [s for s in self._items if s.user_id == user_id and s.is_valid(now)]

    def revoke(self, token: str) -> None:
        """Log a session out. Revoking an unknown or already-revoked token is a no-op, so
        logout is idempotent (clients retry it on flaky networks)."""
        try:
            session = self._by_token.pop(token)
        except KeyError:
            return
        self._items.remove(session)

    def purge_expired(self, now: datetime) -> int:
        """Drop expired sessions to bound memory. Returns how many were removed."""
        removed = 0
        for i in range(len(self._items) - 1, -1, -1):
            session = self._items[i]
            if session.expires_at <= now:
                del self._items[i]
                del self._by_token[session.token]
                removed += 1
        return removed

    def __len__(self) -> int:
        return len(self._items)
