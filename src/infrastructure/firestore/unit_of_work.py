"""Firestore接続とリポジトリを管理するユニットオブワーク。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import App, credentials, firestore

from db.constants import COLLECTION_SENTINEL_DOCUMENT_ID, REQUIRED_COLLECTIONS

from .repositories import (
    HistoryRepository,
    InfoRepository,
    SharedTemplateRepository,
    UserRepository,
)

FirestoreClient = firestore.firestore.Client


class FirestoreUnitOfWork:
    """Firestore クライアントと各種リポジトリのライフサイクルを管理する。"""

    def __init__(self) -> None:
        self._app: App | None = None
        self._client: FirestoreClient | None = None
        self.user_repository: UserRepository | None = None
        self.info_repository: InfoRepository | None = None
        self.shared_template_repository: SharedTemplateRepository | None = None
        self.history_repository: HistoryRepository | None = None

    @property
    def app(self) -> App | None:
        return self._app

    @property
    def client(self) -> FirestoreClient | None:
        return self._client

    @client.setter
    def client(self, value: FirestoreClient | None) -> None:
        self._client = value

    def initialize(self, credentials_source: dict[str, Any] | Path) -> None:
        if self._app is not None:
            raise RuntimeError("FirestoreUnitOfWork is already initialized")

        certificate_source: dict[str, Any] | str
        if isinstance(credentials_source, Path):
            certificate_source = str(credentials_source)
        else:
            certificate_source = credentials_source

        app = firebase_admin.initialize_app(credentials.Certificate(certificate_source))
        self.with_app(app)

    def with_app(self, app: App) -> None:
        if self._app is not None and self._app is not app:
            raise RuntimeError(
                "FirestoreUnitOfWork is already initialized with a different Firebase app"
            )

        self._app = app
        client = firestore.client(app=app)
        self._attach_client(client)

    def with_client(self, client: FirestoreClient) -> None:
        if self._client is not None and self._client is not client:
            raise RuntimeError(
                "FirestoreUnitOfWork is already initialized with a different Firestore client"
            )
        self._attach_client(client)

    def _attach_client(self, client: FirestoreClient) -> None:
        self._client = client
        self.user_repository = UserRepository(client)
        self.info_repository = InfoRepository(client)
        self.shared_template_repository = SharedTemplateRepository(client)
        self.history_repository = HistoryRepository(client)
        self.ensure_required_collections()

    @property
    def is_configured(self) -> bool:
        return all(
            (
                self._client,
                self.user_repository,
                self.info_repository,
                self.history_repository,
            )
        )

    def ensure_configured(self) -> None:
        if not self.is_configured:
            raise RuntimeError(
                "FirestoreUnitOfWork is not configured. Call initialize() or with_app() before use."
            )

    def ensure_required_collections(self) -> None:
        if self._client is None:
            raise RuntimeError(
                "FirestoreUnitOfWork is not configured. Call initialize() or with_app() before use."
            )

        sentinel_payload = {
            "_system": True,
            "_purpose": "collection_sentinel",
            "created_at": datetime.now(timezone.utc),
        }

        for collection_name in REQUIRED_COLLECTIONS:
            collection_ref = self._client.collection(collection_name)
            document_ref = collection_ref.document(COLLECTION_SENTINEL_DOCUMENT_ID)
            snapshot = document_ref.get()
            if not getattr(snapshot, "exists", False):
                document_ref.set(sentinel_payload)


__all__ = ["FirestoreUnitOfWork"]
