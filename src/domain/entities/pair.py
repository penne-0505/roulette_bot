"""ペアリング関連の値オブジェクト。"""

from __future__ import annotations

from dataclasses import dataclass

import discord


@dataclass(slots=True)
class Pair:
    """ユーザーと選択肢のペア。"""

    user: discord.User
    choice: str


@dataclass(slots=True)
class PairList:
    """ペアのコレクション。"""

    pairs: list[Pair]


__all__ = ["Pair", "PairList"]
