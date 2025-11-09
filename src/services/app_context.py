"""アプリケーション起動時のコンテキストセットアップ。"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from db_manager import DBManager
from domain.interfaces.repositories import TemplateRepository
from infrastructure.config.firebase_credentials import resolve_firebase_credentials


def create_db_manager(
    credentials_reference: str | Path | None = None,
    *,
    resolver: Callable[[str | Path | None], Any] | None = None,
) -> TemplateRepository:
    """DBManager を生成し初期化する。"""

    manager = DBManager.get_instance()
    if manager.is_configured:
        return manager

    resolve = resolver or resolve_firebase_credentials
    credentials_source = resolve(credentials_reference)
    manager.initialize(credentials_source)
    return manager


__all__ = ["create_db_manager"]
