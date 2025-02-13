from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import discord
import utils


class AmidakujiState(Enum):
    MEMBER_SELECTED = auto()

    MODE_USE_EXISTING = auto()
    MODE_CREATE_NEW = auto()
    MODE_USE_HISTORY = auto()

    TEMPLATE_SELECTED = auto()
    TEMPLATE_CREATED = auto()


@dataclass
class CommandContext:
    interaction: discord.Interaction
    state: AmidakujiState
    result: Any
    history: dict[AmidakujiState, Any] = field(default_factory=dict)

    def add_to_history(self, state: AmidakujiState, result: Any):
        self.history[state] = result


@dataclass
class Template:
    title: str
    id: str = field(default_factory=lambda: None)  # 初期値をNoneに設定
    choices: list[str]

    def __post_init__(self):
        if self.id is None:
            self.id = utils.gen_template_id(self.title)


@dataclass
class UserInfo:
    id: int
    name: str
    least_template: Template | None = field(default=None)
    custom_templates: list[Template] = field(default_factory=list)


if __name__ == "__main__":
    pass
