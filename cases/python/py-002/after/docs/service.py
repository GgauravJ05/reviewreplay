"""Document operations for the API layer. Every operation acts on behalf of `user_id`."""
from __future__ import annotations

from .repo import Document, DocumentRepo, NotFound


class DocumentService:
    def __init__(self, repo: DocumentRepo) -> None:
        self.repo = repo

    def _owned(self, user_id: int, doc_id: int) -> Document:
        """Fetch a document the user owns. Raises NotFound for other users' documents,
        so the API never reveals which ids exist."""
        doc = self.repo.get(doc_id)
        if doc.owner_id != user_id:
            raise NotFound(doc_id)
        return doc

    def read(self, user_id: int, doc_id: int) -> Document:
        return self._owned(user_id, doc_id)

    def update_body(self, user_id: int, doc_id: int, body: str) -> Document:
        doc = self._owned(user_id, doc_id)
        doc.body = body
        self.repo.save(doc)
        return doc

    def delete(self, user_id: int, doc_id: int) -> None:
        self._owned(user_id, doc_id)
        self.repo.delete(doc_id)

    def rename(self, user_id: int, doc_id: int, title: str) -> Document:
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        if len(title) > 200:
            raise ValueError("title too long")
        document = self.repo.get(doc_id)
        document.title = title
        self.repo.save(document)
        return document
