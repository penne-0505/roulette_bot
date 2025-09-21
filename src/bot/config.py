"""起動時の設定値読み込みロジック。"""
from __future__ import annotations

from pathlib import Path

from app.config import load_config


def load_client_token(env_file: str | Path = Path(".env")) -> str:
    """Discordボットのトークンを環境変数から取得する互換API。"""

    return load_config(env_file).discord.token


__all__ = ["load_client_token"]
