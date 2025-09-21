"""起動時の設定値読み込みロジック。"""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from utils import INFO


def load_client_token(env_file: str | Path = Path(".env")) -> str:
    """Discordボットのトークンを環境変数から読み込む。"""

    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logging.warning(
            INFO + "`.env` file not found. Falling back to environment variables."
        )

    token_raw = os.getenv("CLIENT_TOKEN")
    if token_raw is None:
        raise RuntimeError("CLIENT_TOKEN not found in environment variables.")

    token = token_raw.strip()
    if not token:
        raise RuntimeError("CLIENT_TOKEN environment variable is empty after trimming whitespace.")

    if token != token_raw:
        logging.warning(
            INFO + "CLIENT_TOKEN contained leading/trailing whitespace; trimmed before use."
        )

    token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
    token_length = len(token)
    logging.info(
        INFO
        + f"CLIENT_TOKEN detected (length={token_length}, sha256_prefix={token_digest})."
    )

    if token.count(".") != 2:
        logging.warning(
            INFO
            + "CLIENT_TOKEN does not match the expected Discord bot token format (two dots)."
        )

    return token
