"""Backward compatibility re-export for Firestore repositories."""
from __future__ import annotations

from infrastructure.firestore.repositories import (
    FirestoreRepository,
    HistoryRepository,
    InfoRepository,
    SharedTemplateRepository,
    UserRepository,
)

__all__ = [
    "FirestoreRepository",
    "UserRepository",
    "InfoRepository",
    "SharedTemplateRepository",
    "HistoryRepository",
]
