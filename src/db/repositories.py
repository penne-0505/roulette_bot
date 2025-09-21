"""Firestore向けのリポジトリクラス群。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from firebase_admin import firestore
from google.api_core import exceptions as google_exceptions

from .constants import COLLECTION_SENTINEL_DOCUMENT_ID
from .serializers import ensure_datetime

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
        template_id = str(data.get("template_id") or "").strip()
        document_ref: DocumentReference
        if template_id:
            document_ref = self.ref.document(template_id)
        else:
            document_ref = self.ref.document()
            template_id = document_ref.id
            data["template_id"] = template_id

        document_ref.set(data)
        return template_id

    def delete_template(self, template_id: str) -> None:
        self.document(template_id).delete()

    def list_templates(
        self,
        *,
        scope: str | None = None,
        guild_id: int | None = None,
        created_by: int | None = None,
    ) -> list[Any]:
        query: Query | CollectionReference = self.ref
        if scope is not None:
            query = query.where("scope", "==", scope)
        if guild_id is not None:
            query = query.where("guild_id", "==", guild_id)
        if created_by is not None:
            query = query.where("created_by", "==", created_by)

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
        if since is not None and since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

        base_query: Query = self.ref.where("guild_id", "==", guild_id)

        query: Query = base_query
        if since is not None:
            query = query.where("created_at", ">=", since)
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        if template_title is None and limit:
            query = query.limit(limit)

        try:
            snapshots = list(query.stream())
        except google_exceptions.FailedPrecondition:
            snapshots = list(base_query.stream())

        def _normalize_created_at(value: Any) -> datetime | None:
            normalized = ensure_datetime(value)
            if normalized is None:
                return None
            if normalized.tzinfo is None:
                return normalized.replace(tzinfo=timezone.utc)
            return normalized

        filtered: list[tuple[datetime | None, dict]] = []
        for snapshot in snapshots:
            data = snapshot.to_dict()
            if not isinstance(data, dict):
                continue
            created_at_value = data.get("created_at")
            created_at_dt = _normalize_created_at(created_at_value)
            if since is not None and created_at_dt is not None and created_at_dt < since:
                continue
            if template_title is not None and data.get("template_title") != template_title:
                continue
            filtered.append((created_at_dt, data))

        filtered.sort(
            key=lambda item: item[0] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        if limit:
            filtered = filtered[:limit]

        return [data for _, data in filtered]


__all__ = [
    "FirestoreRepository",
    "UserRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "HistoryRepository",
]
