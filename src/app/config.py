from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from utils import INFO


@dataclass(frozen=True, slots=True)
class DiscordSettings:
    """Discord 関連の設定値。"""

    token: str


@dataclass(frozen=True, slots=True)
class FirebaseSettings:
    """Firebase 関連の設定値。"""

    credentials_reference: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    """アプリケーション全体の設定値を集約したデータクラス。"""

    discord: DiscordSettings
    firebase: FirebaseSettings


def _load_env_file(env_file: str | Path | None) -> None:
    if env_file is None:
        load_dotenv()
        return

    path = Path(env_file)
    if path.exists():
        load_dotenv(path)
    else:
        logging.warning(
            INFO + f"Environment file '{path}' not found. Falling back to process env."
        )


def _prepare_client_token(raw_token: str | None) -> str:
    if raw_token is None:
        raise RuntimeError("CLIENT_TOKEN not found in environment variables.")

    token = raw_token.strip()
    if not token:
        raise RuntimeError("CLIENT_TOKEN environment variable is empty after trimming whitespace.")

    if token != raw_token:
        logging.warning(
            INFO + "CLIENT_TOKEN contained leading/trailing whitespace; trimmed before use."
        )

    token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
    logging.info(
        INFO
        + f"CLIENT_TOKEN detected (length={len(token)}, sha256_prefix={token_digest})."
    )

    if token.count(".") != 2:
        logging.warning(
            INFO
            + "CLIENT_TOKEN does not match the expected Discord bot token format (two dots)."
        )

    return token


def _prepare_firebase_reference(raw_reference: str | None) -> str:
    if raw_reference is None:
        raise RuntimeError("FIREBASE_CREDENTIALS is not set")

    reference = raw_reference.strip()
    if not reference:
        raise RuntimeError("FIREBASE_CREDENTIALS is empty after trimming whitespace.")

    return reference


def load_config(env_file: str | Path | None = Path(".env")) -> AppConfig:
    """環境変数からアプリケーション設定を読み込む。"""

    _load_env_file(env_file)

    token = _prepare_client_token(os.getenv("CLIENT_TOKEN"))
    firebase_reference = _prepare_firebase_reference(os.getenv("FIREBASE_CREDENTIALS"))

    return AppConfig(
        discord=DiscordSettings(token=token),
        firebase=FirebaseSettings(credentials_reference=firebase_reference),
    )


__all__ = [
    "AppConfig",
    "DiscordSettings",
    "FirebaseSettings",
    "load_config",
]
