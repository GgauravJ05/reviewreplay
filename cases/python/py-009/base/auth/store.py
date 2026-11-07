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

    def __len__(self) -> int:
        return len(self._items)
