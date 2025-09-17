from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from db_manager import DBManager


def load_firebase_credentials() -> dict[str, Any] | Path:
    """Load Firebase credentials from the environment."""
    load_dotenv()
    credentials_location = os.getenv("FIREBASE_CREDENTIALS")
    if not credentials_location:
        raise RuntimeError("FIREBASE_CREDENTIALS is not set")

    credentials_path = Path(credentials_location)
    if credentials_path.exists():
        return credentials_path

    response = requests.get(credentials_location, timeout=30)
    response.raise_for_status()
    return response.json()


def create_db_manager() -> DBManager:
    """Create and initialize a DBManager instance."""
    manager = DBManager.get_instance()
    if manager.db is not None:
        return manager

    credentials_source = load_firebase_credentials()
    manager.initialize(credentials_source)
    return manager
