from __future__ import annotations

import logging
from typing import Any

from utils import DATEFORMAT, FORMAT


def configure_logging(level: int | str | None = None, **kwargs: Any) -> None:
    """ロギング設定を初期化するための薄いラッパー。"""

    logging.basicConfig(
        level=logging.INFO if level is None else level,
        format=FORMAT,
        datefmt=DATEFORMAT,
        **kwargs,
    )


__all__ = ["configure_logging"]
