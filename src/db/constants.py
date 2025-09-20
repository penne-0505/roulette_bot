"""Firestoreコレクションに関する定数を集約したモジュール。"""
from __future__ import annotations

COLLECTION_SENTINEL_DOCUMENT_ID = "__collection_init__"
REQUIRED_COLLECTIONS: tuple[str, ...] = (
    "users",
    "info",
    "shared_templates",
    "history",
)

__all__ = [
    "COLLECTION_SENTINEL_DOCUMENT_ID",
    "REQUIRED_COLLECTIONS",
]
