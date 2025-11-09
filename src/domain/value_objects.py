"""小さな値オブジェクト群。"""

from __future__ import annotations

from enum import Enum


class ResultEmbedMode(Enum):
    """結果埋め込みの表示モード。"""

    COMPACT = "compact"
    DETAILED = "detailed"


__all__ = ["ResultEmbedMode"]
