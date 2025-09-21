from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from db_manager import DBManager


def resolve_firebase_credentials(
    credentials_reference: str | Path | None = None,
) -> dict[str, Any] | Path:
    """Resolve Firebase credentials from a path, URL, or environment variable."""

    if credentials_reference is None:
        load_dotenv()
        credentials_reference = os.getenv("FIREBASE_CREDENTIALS")

    if credentials_reference is None or not str(credentials_reference).strip():
        raise RuntimeError("FIREBASE_CREDENTIALS is not set")

    reference = Path(credentials_reference)
    if reference.exists():
        return reference

    response = requests.get(str(credentials_reference), timeout=30)
    response.raise_for_status()
    return response.json()


def create_db_manager(
    credentials_reference: str | Path | None = None,
) -> DBManager:
    """Create and initialize a DBManager instance."""

    manager = DBManager.get_instance()
    if manager.db is not None:
        return manager

    credentials_source = resolve_firebase_credentials(credentials_reference)
    manager.initialize(credentials_source)
    return manager
