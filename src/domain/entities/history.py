"""履歴および関連値オブジェクト。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SelectionMode(Enum):
    """メンバー割当の方式。"""

    RANDOM = "random"
    BIAS_REDUCTION = "bias_reduction"


@dataclass(slots=True)
class AssignmentEntry:
    """割当結果の 1 件。"""

    user_id: int
    user_name: str
    choice: str


@dataclass(slots=True)
class AssignmentHistory:
    """割当結果の履歴。"""

    guild_id: int
    template_title: str
    created_at: datetime
    entries: list[AssignmentEntry]
    choices: list[str] = field(default_factory=list)
    selection_mode: SelectionMode = SelectionMode.RANDOM


__all__ = ["AssignmentEntry", "AssignmentHistory", "SelectionMode"]
