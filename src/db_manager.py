"""DBManager の後方互換ラッパー。"""
from __future__ import annotations

from typing import ClassVar

from db.constants import COLLECTION_SENTINEL_DOCUMENT_ID, REQUIRED_COLLECTIONS
from db.repositories import (
    HistoryRepository,
    InfoRepository,
    SharedTemplateRepository,
    UserRepository,
)
from infrastructure.firestore.template_repository import FirestoreTemplateRepository
from infrastructure.firestore.unit_of_work import FirestoreUnitOfWork


class DBManager(FirestoreTemplateRepository):
    """従来の DBManager API を維持する FirestoreTemplateRepository ラッパー。"""

    _global_instance: ClassVar["DBManager | None"] = None

    def __init__(self, *, unit_of_work: FirestoreUnitOfWork | None = None) -> None:
        super().__init__(unit_of_work=unit_of_work or FirestoreUnitOfWork())

    @classmethod
    def get_instance(cls) -> "DBManager":
        if cls._global_instance is None:
            cls._global_instance = cls()
        return cls._global_instance

    @classmethod
    def set_global_instance(cls, instance: "DBManager" | None) -> None:
        cls._global_instance = instance


__all__ = [
    "DBManager",
    "COLLECTION_SENTINEL_DOCUMENT_ID",
    "REQUIRED_COLLECTIONS",
    "UserRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "HistoryRepository",
]
