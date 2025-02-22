from enum import Enum
from typing import List, TypeAlias, Union

import discord
from model.model import Template


class AmidakujiStateTypes(Enum):
    EXPECTED_TYPES: TypeAlias = Union[
        discord.Interaction, str, int, Template, List[discord.User]
    ]

    COMMAND_EXECUTED: TypeAlias = discord.Interaction

    MODE_USE_EXISTING: TypeAlias = discord.Interaction
    MODE_CREATE_NEW: TypeAlias = discord.Interaction
    MODE_USE_HISTORY: TypeAlias = discord.Interaction

    TEMPLATE_TITLE_ENTERED: TypeAlias = str
    OPTIONS_COUNT_ENTERED: TypeAlias = int
    NEED_MORE_OPTIONS: TypeAlias = discord.Interaction
    TEMPLATE_CREATED: TypeAlias = Template

    TEMPLATE_DETERMINED: TypeAlias = Template

    MEMBER_SELECTED: TypeAlias = List[discord.User]

    RESULT_DISPLAYED: TypeAlias = discord.Interaction

    HISTORY_SAVED: TypeAlias = discord.Interaction

    CANCELLED: TypeAlias = discord.Interaction


if __name__ == "__main__":
    pass
