from dataclasses import dataclass, field
from typing import Union

import discord
import utils


@dataclass
class Template:
    """
    テンプレートのデータモデル。DBに保存するときもこの形式を使う。
    """

    title: str
    id: str = field(default_factory=lambda: None)  # 初期値をNoneに設定
    choices: list[str]

    def __post_init__(self):
        if self.id is None:
            self.id = utils.gen_template_id(self.title)


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


TRUE_RESULT_TYPES = Union[
    discord.Interaction | str | int | Template | list[discord.User]
]


if __name__ == "__main__":
    pass
