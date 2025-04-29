from dataclasses import dataclass, field
from enum import Enum

import discord


@dataclass
class Template:
    title: str
    choices: list[str]


@dataclass
class UserInfo:
    id: int
    name: str
    least_template: Template | None = field(default=None)
    custom_templates: list[Template] = field(default_factory=list)


@dataclass
class Pair:
    user: discord.User
    choice: str


@dataclass
class PairList:
    pairs: list[Pair]


class ResultEmbedMode(Enum):
    COMPACT = "compact"
    DETAILED = "detailed"


if __name__ == "__main__":
    pass
