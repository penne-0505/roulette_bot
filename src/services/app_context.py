"""アプリケーション起動時のコンテキストセットアップ。"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from domain.interfaces.repositories import TemplateRepository
from infrastructure.config.firebase_credentials import resolve_firebase_credentials
from infrastructure.firestore.template_repository import FirestoreTemplateRepository

_template_repository: FirestoreTemplateRepository | None = None


def _get_repository_instance() -> FirestoreTemplateRepository:
    global _template_repository
    if _template_repository is None:
        _template_repository = FirestoreTemplateRepository()
    return _template_repository


def create_template_repository(
    credentials_reference: str | Path | None = None,
    *,
    resolver: Callable[[str | Path | None], Any] | None = None,
) -> TemplateRepository:
    """FirestoreTemplateRepository を初期化し、シングルトンとして返す。"""

    repository = _get_repository_instance()
    if repository.is_configured:
        return repository

    resolve = resolver or resolve_firebase_credentials
    credentials_source = resolve(credentials_reference)
    repository.initialize(credentials_source)
    return repository


def reset_template_repository() -> None:
    """テスト向けに保持中のリポジトリインスタンスをリセットする。"""

    global _template_repository
    _template_repository = None


__all__ = ["create_template_repository", "reset_template_repository"]
