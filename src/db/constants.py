"""Firestoreコレクションに関する定数を集約したモジュール。"""
from __future__ import annotations

# Firestoreでは先頭が"__"のドキュメントIDが予約されているため避ける。
COLLECTION_SENTINEL_DOCUMENT_ID = "collection_init_sentinel"
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
