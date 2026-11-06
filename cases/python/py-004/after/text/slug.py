"""URL slugs."""
from __future__ import annotations

import re
import unicodedata


def slugify(title: str) -> str:
    """ASCII, lowercase, hyphen-separated, never empty."""
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "untitled"


def unique_slug(title: str, taken: set[str]) -> str:
    """slugify(title), with -2, -3, ... appended if needed so the result is not in `taken`."""
    base = slugify(title)
    candidate = base
    n = 2
    while candidate in taken:
        candidate = f"{base}-{n}"
        n += 1
    return candidate
