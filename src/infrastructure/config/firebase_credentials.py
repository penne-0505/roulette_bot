"""Firebase 認証情報の解決ユーティリティ。"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

DEFAULT_TIMEOUT = 30
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "roulette_bot" / "firebase"
LOGGER = logging.getLogger(__name__)


def _default_http_get(url: str) -> requests.Response:
    return requests.get(url, timeout=DEFAULT_TIMEOUT)


def _is_http_reference(reference: str) -> bool:
    parsed = urlparse(reference)
    return parsed.scheme.lower() in {"http", "https"}


def _build_cache_path(reference: str, base_dir: Path | None) -> Path:
    target_dir = (base_dir or DEFAULT_CACHE_DIR).expanduser()
    digest = hashlib.sha256(reference.encode("utf-8")).hexdigest()
    return target_dir / f"{digest}.json"


def _load_cached_credentials(cache_path: Path) -> dict[str, Any] | None:
    if not cache_path.exists():
        return None
    try:
        with cache_path.open("r", encoding="utf-8") as cached:
            return json.load(cached)
    except (OSError, json.JSONDecodeError):
        return None


def _store_cached_credentials(cache_path: Path, payload: dict[str, Any]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as target:
        json.dump(payload, target)


def _fetch_remote_credentials(
    reference: str, fetcher: Callable[[str], requests.Response]
) -> dict[str, Any]:
    response = fetcher(reference)
    response.raise_for_status()
    return response.json()


def resolve_firebase_credentials(
    credentials_reference: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    env_loader: Callable[[], None] | None = load_dotenv,
    http_get: Callable[[str], requests.Response] | None = None,
    cache_dir: Path | None = None,
    enable_cache: bool = True,
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
    reference_str = str(reference)
    should_use_cache = enable_cache and _is_http_reference(reference_str)

    if should_use_cache:
        cache_path = _build_cache_path(reference_str, cache_dir)
        cached_payload = _load_cached_credentials(cache_path)
        if cached_payload is not None:
            LOGGER.debug("Resolved Firebase credentials from cache: %s", reference_str)
            return cached_payload

        payload = _fetch_remote_credentials(reference_str, fetch)
        try:
            _store_cached_credentials(cache_path, payload)
        except OSError:
            LOGGER.debug("Failed to persist Firebase credentials cache: %s", cache_path)
        else:
            LOGGER.debug("Cached Firebase credentials at %s", cache_path)
        return payload

    return _fetch_remote_credentials(reference_str, fetch)


__all__ = ["resolve_firebase_credentials"]
