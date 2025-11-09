"""Firebase 認証情報の解決ユーティリティ。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping

import requests
from dotenv import load_dotenv

DEFAULT_TIMEOUT = 30


def _default_http_get(url: str) -> requests.Response:
    return requests.get(url, timeout=DEFAULT_TIMEOUT)


def resolve_firebase_credentials(
    credentials_reference: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    env_loader: Callable[[], None] | None = load_dotenv,
    http_get: Callable[[str], requests.Response] | None = None,
) -> dict[str, Any] | Path:
    """パス・URL・環境変数から Firebase 認証情報を解決する。"""

    reference = credentials_reference
    if reference is None:
        if env is None:
            if env_loader is not None:
                env_loader()
            env = os.environ
        else:
            if env_loader is not None:
                env_loader()
        reference = env.get("FIREBASE_CREDENTIALS") if env is not None else None

    if reference is None or not str(reference).strip():
        raise RuntimeError("FIREBASE_CREDENTIALS is not set")

    path_candidate = Path(str(reference))
    if path_candidate.exists():
        return path_candidate

    fetch = http_get or _default_http_get
    response = fetch(str(reference))
    response.raise_for_status()
    return response.json()


__all__ = ["resolve_firebase_credentials"]
