"""Firestore周りのサブパッケージ。"""
from .constants import COLLECTION_SENTINEL_DOCUMENT_ID, REQUIRED_COLLECTIONS
from .repositories import (
    FirestoreRepository,
    HistoryRepository,
    InfoRepository,
    SharedTemplateRepository,
    UserRepository,
)
from .serializers import (
    deserialize_assignment_history,
    deserialize_template,
    ensure_datetime,
    normalize_template_for_user,
    serialize_template,
)

__all__ = [
    "COLLECTION_SENTINEL_DOCUMENT_ID",
    "REQUIRED_COLLECTIONS",
    "FirestoreRepository",
    "HistoryRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "UserRepository",
    "deserialize_assignment_history",
    "deserialize_template",
    "ensure_datetime",
    "normalize_template_for_user",
    "serialize_template",
]
