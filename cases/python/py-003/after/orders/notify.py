"""Customer notifications."""
from __future__ import annotations


class Mailer:
    def send(self, to: str, subject: str, body: str) -> None:  # pragma: no cover - real SMTP
        raise NotImplementedError
