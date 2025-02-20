from typing import TypedDict

import discord
from model.model import Template

class AmidakujiStateTypes(TypedDict, total=False):
    EXPECTED_TYPES: discord.Interaction | str | int | Template | list[discord.User]

    COMMAND_EXECUTED: discord.Interaction

    MODE_USE_EXISTING: discord.Interaction
    MODE_CREATE_NEW: discord.Interaction
    MODE_USE_HISTORY: discord.Interaction

    TEMPLATE_TITLE_ENTERED: str
    OPTIONS_COUNT_ENTERED: int
    NEED_MORE_OPTIONS: discord.Interaction
    TEMPLATE_CREATED: Template

    TEMPLATE_DETERMINED: Template

    MEMBER_SELECTED: list[discord.User]

    RESULT_DISPLAYED: discord.Interaction

    HISTORY_SAVED: discord.Interaction

    CANCELLED: discord.Interaction
