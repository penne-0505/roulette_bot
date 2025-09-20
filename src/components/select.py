from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, TypeVar


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


class _TemplateSelectBase(discord.ui.Select):
    def __init__(
        self,
        context: CommandContext,
        templates: list[Template],
        *,
        placeholder: str,
    ) -> None:
        options = [
            discord.SelectOption(label=template.title, value=str(index))
            for index, template in enumerate(templates)
        ]
        super().__init__(placeholder=placeholder, options=options)
        self.context = context
        self._template_map: dict[str, Template] = {
            option.value: template for option, template in zip(self.options, templates)
        }

    def _resolve_template(self) -> Template:
        selected_value = self.values[0]
        template = self._template_map.get(selected_value)
        if template is None:
            raise ValueError("Template is not selected")
        return template


class TemplateSelect(_TemplateSelectBase):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(
            context,
            templates,
            placeholder="テンプレートを選択してください",
        )

    async def callback(self, interaction: discord.Interaction):
        selected_template = self._resolve_template()
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_DETERMINED,
            selected_template,
            interaction,
        )


class SharedTemplateSelect(_TemplateSelectBase):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(
            context,
            templates,
            placeholder="共有テンプレートを選択してください",
        )

    async def callback(self, interaction: discord.Interaction):
        template = self._resolve_template()
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.SHARED_TEMPLATE_SELECTED,
            template,
            interaction,
        )


class PublicTemplateSelect(_TemplateSelectBase):
    def __init__(self, context: CommandContext, templates: list[Template]):
        super().__init__(
            context,
            templates,
            placeholder="公開テンプレートを選択してください",
        )

    async def callback(self, interaction: discord.Interaction):
        template = self._resolve_template()
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.SHARED_TEMPLATE_SELECTED,
            template,
            interaction,
        )


class TemplateDeleteSelect(discord.ui.Select):
    def __init__(self, context: CommandContext, templates: list[Template]):
        if not templates:
            raise ValueError("Templates must not be empty")

        super().__init__(
            placeholder="削除するテンプレートを選択してください",
            options=[discord.SelectOption(label=template.title) for template in templates],
        )
        self.context = context

    async def callback(self, interaction: discord.Interaction):
        selected_template_title = self.values[0]
        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.TEMPLATE_DELETED,
            selected_template_title,
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
        result = remove_bots([user for user in result if user is not None])

        flow = _get_flow(self.context)
        await flow.dispatch(
            AmidakujiState.MEMBER_SELECTED,
            result,
            interaction,
        )
