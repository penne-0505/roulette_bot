"""Firestore向けのリポジトリクラス群。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from firebase_admin import firestore

from .constants import COLLECTION_SENTINEL_DOCUMENT_ID

FirestoreClient = firestore.firestore.Client
CollectionReference = firestore.CollectionReference
DocumentReference = firestore.DocumentReference
Query = firestore.Query


class FirestoreRepository:
    """Firestoreの単一コレクションに対する基本的な操作を提供する。"""

    def __init__(self, client: FirestoreClient, collection_name: str) -> None:
        self._client = client
        self.ref: CollectionReference = client.collection(collection_name)

    def document(self, document_id: str) -> DocumentReference:
        return self.ref.document(str(document_id))


class UserRepository(FirestoreRepository):
    """`users` コレクションを操作するリポジトリ。"""

    def __init__(self, client: FirestoreClient) -> None:
        super().__init__(client, "users")

    def create_document(self, doc_id: int | str, data: dict) -> None:
        document = self.document(str(doc_id))
        document.set(data)

    def read_document(self, doc_id: int | str) -> dict | None:
        snapshot = self.document(str(doc_id)).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()

    def delete_document(self, doc_id: int | str) -> None:
        self.document(str(doc_id)).delete()


class InfoRepository(FirestoreRepository):
    """`info` コレクションを操作するリポジトリ。"""

    def __init__(self, client: FirestoreClient) -> None:
        super().__init__(client, "info")

    def create_document(self, doc_id: int | str, data: dict) -> None:
        document = self.document(str(doc_id))
        document.set(data)

    def read_document(self, doc_id: int | str) -> dict | None:
        snapshot = self.document(str(doc_id)).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()


class SharedTemplateRepository(FirestoreRepository):
    """`shared_templates` コレクションを操作するリポジトリ。"""

    def __init__(self, client: FirestoreClient) -> None:
        super().__init__(client, "shared_templates")

    def add_template(self, data: dict[str, Any]) -> str:
        document_ref = self.ref.document()
        document_ref.set(data)
        return document_ref.id

    def delete_template(self, template_id: str) -> None:
        self.document(template_id).delete()

    def list_templates(
        self,
        *,
        scope: str | None = None,
        guild_id: int | None = None,
    ) -> list[Any]:
        query: Query | CollectionReference = self.ref
        if scope is not None:
            query = query.where("scope", "==", scope)
        if guild_id is not None:
            query = query.where("guild_id", "==", guild_id)

        documents: list[Any] = []
        for document in query.stream():
            if getattr(document, "id", None) == COLLECTION_SENTINEL_DOCUMENT_ID:
                continue
            documents.append(document)
        return documents

    def read_document(self, doc_id: int | str) -> dict | None:
        snapshot = self.document(str(doc_id)).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()


class HistoryRepository(FirestoreRepository):
    """`history` コレクションを操作するリポジトリ。"""

    def __init__(self, client: FirestoreClient) -> None:
        super().__init__(client, "history")

    def add_entry(self, data: dict) -> None:
        document = self.ref.document()
        document.set(data)

    def fetch_recent(
        self,
        *,
        guild_id: int,
        template_title: str | None = None,
        limit: int = 10,
        since: datetime | None = None,
    ) -> list[dict]:
        query: Query = self.ref.where("guild_id", "==", guild_id)
        if template_title is not None:
            query = query.where("template_title", "==", template_title)
        if since is not None:
            query = query.where("created_at", ">=", since)
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        if limit:
            query = query.limit(limit)
        return [doc.to_dict() for doc in query.stream()]


__all__ = [
    "FirestoreRepository",
    "UserRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "HistoryRepository",
]
