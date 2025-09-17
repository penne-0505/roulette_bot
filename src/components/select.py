from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeVar

import discord

from db_manager import db
from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState

if TYPE_CHECKING:
    from data_interface import DataInterface
    from db_manager import DBManager


def _get_flow(context: CommandContext):
    services = context.services
    flow = getattr(services, "flow", None) if services is not None else None
    if flow is None:
        raise RuntimeError("Flow controller is not available")
    return flow


class TemplateSelect(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(
            placeholder="テンプレートを選択してください",
            options=[
                discord.SelectOption(label=template.title) for template in templates
            ],
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        selected_template_title = self.values[0]
        current_user = db.get_user(interaction.user.id)
        user_templates = current_user.custom_templates if current_user else []
        selected_template = next(
            (t for t in user_templates if t.title == selected_template_title),
            None,
        )

        if selected_template is None:
            raise ValueError("Template is not selected")

        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_DETERMINED,
            selected_template,
            interaction,
        )


T = TypeVar("T")


def remove_bots(users: Iterable[T]) -> list[T]:
    """Return users without bot accounts.

    Both ``discord.User`` and ``discord.Member`` expose a ``bot`` attribute, but
    it may be missing for custom implementations in tests.  ``getattr`` with a
    default ensures that we treat objects without the attribute as non-bot
    users.
    """

    return [user for user in users if not getattr(user, "bot", False)]


class MemberSelect(discord.ui.UserSelect):
    def __init__(self, context: CommandContext):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        result = []
        for user in self.values:
            if isinstance(user, discord.User):
                result.append(user)
            elif isinstance(user, discord.Member):
                resolved_user = interaction.client.get_user(user.id)
                if resolved_user is None:
                    try:
                        resolved_user = await interaction.client.fetch_user(user.id)
                    except discord.DiscordException:
                        resolved_user = None
                if resolved_user is not None:
                    result.append(resolved_user)
        result = [user for user in result if user is not None and not user.bot]

        flow = _get_flow(self.context
        await flow.dispatch(
            AmidakujiState.MEMBER_SELECTED,
            result,
            interaction,
        )
