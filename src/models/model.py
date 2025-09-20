from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import discord


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
    template_id: str | None = None
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


# TODO: これはどこに置くべき？
class ResultEmbedMode(Enum):
    COMPACT = "compact"
    DETAILED = "detailed"


if __name__ == "__main__":
    pass
