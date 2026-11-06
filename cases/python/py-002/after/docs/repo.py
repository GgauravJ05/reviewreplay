"""In-memory document store (stands in for the database)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document:
    id: int
    owner_id: int
    title: str
    body: str = ""


class NotFound(Exception):
    pass


class DocumentRepo:
    def __init__(self) -> None:
        self._docs: dict[int, Document] = {}
        self._next = 1

    def add(self, owner_id: int, title: str, body: str = "") -> Document:
        doc = Document(self._next, owner_id, title, body)
        self._docs[doc.id] = doc
        self._next += 1
        return doc

    def get(self, doc_id: int) -> Document:
        try:
            return self._docs[doc_id]
        except KeyError:
            raise NotFound(doc_id) from None

    def save(self, doc: Document) -> None:
        self._docs[doc.id] = doc

    def delete(self, doc_id: int) -> None:
        self._docs.pop(doc_id, None)
