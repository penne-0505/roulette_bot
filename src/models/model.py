from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import discord

from utils import generate_template_id

class TemplateScope(Enum):
    """テンプレートの共有範囲を示す列挙体。"""

    PRIVATE = "private"
    GUILD = "guild"
    PUBLIC = "public"


@dataclass
class Template:
    """テンプレートのデータモデル。DBに保存するときもこの形式を使う。"""

    title: str
    choices: list[str]
    scope: TemplateScope = TemplateScope.PRIVATE
    created_by: int | None = None
    guild_id: int | None = None
    template_id: str = field(default_factory=generate_template_id)
    updated_at: datetime | None = None


@dataclass
class UserInfo:
    """
    DBに保存することを前提としたデータモデル。
    DBにわたす時にこの形式に直し、DBから受け取ったユーザー情報、テンプレート情報はこの形式で保持する
    """

    id: int
    name: str
    least_template: Template | None = field(default=None)
    custom_templates: list[Template] = field(default_factory=list)
    shared_templates: list[Template] = field(default_factory=list)
    public_templates: list[Template] = field(default_factory=list)


@dataclass
class Pair:
    """
    ペアのデータモデル。
    """

    user: discord.User
    choice: str


@dataclass
class PairList:
    """
    ペアのリストのデータモデル。
    """

    pairs: list[Pair]


class ResultEmbedMode(Enum):
    """結果埋め込みの表示モード。"""

    COMPACT = "compact"
    DETAILED = "detailed"


class SelectionMode(Enum):
    RANDOM = "random"
    BIAS_REDUCTION = "bias_reduction"


@dataclass
class AssignmentEntry:
    user_id: int
    user_name: str
    choice: str


@dataclass
class AssignmentHistory:
    guild_id: int
    template_title: str
    created_at: datetime
    entries: list[AssignmentEntry]
    choices: list[str] = field(default_factory=list)
    selection_mode: SelectionMode = SelectionMode.RANDOM


if __name__ == "__main__":
    pass
