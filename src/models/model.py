from dataclasses import dataclass, field
from enum import Enum

import discord


@dataclass
class Template:
    """
    テンプレートのデータモデル。DBに保存するときもこの形式を使う。
    """

    # 現状、タイトルの重複は許容できない

    title: str
    choices: list[str]


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
