from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from infrastructure.config.firebase_credentials import resolve_firebase_credentials


class _DummyResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self._raised = False

    def raise_for_status(self) -> None:
        self._raised = True

    def json(self) -> dict[str, Any]:
        return self._payload


def test_resolve_uses_existing_path(tmp_path: Path) -> None:
    credentials_path = tmp_path / "firebase.json"
    credentials_path.write_text("{}", encoding="utf-8")

    resolved = resolve_firebase_credentials(credentials_path)

    assert resolved == credentials_path


def test_resolve_uses_environment_loader(tmp_path: Path) -> None:
    credentials_path = tmp_path / "firebase.json"
    credentials_path.write_text("{}", encoding="utf-8")

    called: list[None] = []

    def fake_loader() -> None:
        called.append(None)

    resolved = resolve_firebase_credentials(
        None,
        env={"FIREBASE_CREDENTIALS": str(credentials_path)},
        env_loader=fake_loader,
    )

    assert resolved == credentials_path
    assert called, "env_loader should be invoked when resolving credentials"


def test_resolve_fetches_from_http_when_not_a_path() -> None:
    payload = {"project_id": "demo"}
    response = _DummyResponse(payload)

    requested: list[str] = []

    def fake_get(url: str) -> _DummyResponse:
        requested.append(url)
        return response

    resolved = resolve_firebase_credentials(
        "https://example.com/firebase.json", http_get=fake_get
    )

    assert resolved == payload
    assert requested == ["https://example.com/firebase.json"]
    assert response._raised is True


def test_resolve_missing_reference_raises_error() -> None:
    with pytest.raises(RuntimeError):
        resolve_firebase_credentials(None, env={}, env_loader=lambda: None)


def test_resolve_http_response_is_cached(tmp_path: Path) -> None:
    payload = {"project_id": "demo"}
    response = _DummyResponse(payload)
    requested: list[str] = []

    def fake_get(url: str) -> _DummyResponse:
        requested.append(url)
        return response

    first = resolve_firebase_credentials(
        "https://example.com/firebase.json",
        http_get=fake_get,
        cache_dir=tmp_path,
    )
    second = resolve_firebase_credentials(
        "https://example.com/firebase.json",
        http_get=fake_get,
        cache_dir=tmp_path,
    )

    assert first == payload
    assert second == payload
    assert requested == ["https://example.com/firebase.json"]


def test_resolve_cache_can_be_disabled(tmp_path: Path) -> None:
    payload = {"project_id": "demo"}
    response = _DummyResponse(payload)
    requested: list[str] = []

    def fake_get(url: str) -> _DummyResponse:
        requested.append(url)
        return response

    resolve_firebase_credentials(
        "https://example.com/firebase.json",
        http_get=fake_get,
        cache_dir=tmp_path,
        enable_cache=False,
    )
    resolve_firebase_credentials(
        "https://example.com/firebase.json",
        http_get=fake_get,
        cache_dir=tmp_path,
        enable_cache=False,
    )

    assert requested == [
        "https://example.com/firebase.json",
        "https://example.com/firebase.json",
    ]
