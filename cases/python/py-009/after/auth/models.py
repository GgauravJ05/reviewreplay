"""Login sessions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Session:
    token: str
    user_id: int
    expires_at: datetime

    def is_valid(self, now: datetime) -> bool:
        """A session is valid while now < expires_at; at expires_at it has expired."""
        return now < self.expires_at
