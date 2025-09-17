from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState

if TYPE_CHECKING:
    from db_manager import DBManager


def _get_flow(context: CommandContext):
    services = context.services
    flow = getattr(services, "flow", None) if services is not None else None
    if flow is None:
        raise RuntimeError("Flow controller is not available")
    return flow


def _get_db_manager(context: CommandContext, interaction: discord.Interaction) -> "DBManager":
    services = context.services
    db_manager = getattr(services, "db", None) if services is not None else None
    if db_manager is None:
        client = getattr(interaction, "client", None)
        db_manager = getattr(client, "db", None) if client is not None else None
    if db_manager is None:
        raise RuntimeError("DB manager is not available")
    return db_manager


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
        db_manager = _get_db_manager(self.context, interaction)
        current_user = db_manager.get_user(interaction.user.id)
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
                result.append(self.context.interaction.client.get_user(user.id))

        result = [user for user in result if user is not None and not user.bot]

        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MEMBER_SELECTED,
            result,
            interaction,
        )
