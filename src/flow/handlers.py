"""State handlers that produce flow actions for Amidakuji interactions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import discord

import data_process
from flow.actions import (
    DeferResponseAction,
    FlowAction,
    SendMessageAction,
    SendViewAction,
    ShowModalAction,
)
from models.context_model import CommandContext
from models.model import Template
from models.state_model import AmidakujiState
from views.view import (
    ApplyOptionsView,
    EnterOptionView,
    MemberSelectView,
    SelectTemplateView,
)
from components.modal import OptionNameEnterModal, TitleEnterModal

if TYPE_CHECKING:
    from db_manager import DBManager


def get_db_manager_from_source(source: Any) -> Any:
    """Helper to safely get the db manager from a source object."""
    return getattr(source, "db", None) if source is not None else None

def resolve_db_manager(context: CommandContext, services: Any) -> "DBManager":
    db_manager = get_db_manager_from_source(services)
    if db_manager is None:
        interaction_client = getattr(context.interaction, "client", None)
        db_manager = get_db_manager_from_source(interaction_client)
    if db_manager is None:
        raise RuntimeError("DB manager is not available")
    return db_manager


class BaseStateHandler(ABC):
    """Base class for state handlers."""

    @abstractmethod
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction] | None:
        """Return actions to execute for the current state."""


class UseExistingHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        target_user = context.interaction.user
        db_manager = resolve_db_manager(context, services)
        user_data = db_manager.get_user(target_user.id)
        templates = user_data.custom_templates if user_data else []

        view = SelectTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class CreateNewHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        modal = TitleEnterModal(context=context)
        return ShowModalAction(modal=modal)


class TemplateTitleEnteredHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        view = EnterOptionView(context=context)
        return SendViewAction(view=view)


class EnterOptionButtonHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        modal = OptionNameEnterModal(context=context)
        return ShowModalAction(modal=modal)


class OptionNameEnteredHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        view = ApplyOptionsView(context=context)
        return SendViewAction(view=view)


class NeedMoreOptionsHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        modal = OptionNameEnterModal(context=context)
        return ShowModalAction(modal=modal)


class TemplateCreatedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        user_id = context.interaction.user.id
        db_manager = resolve_db_manager(context, services)
        db_manager.add_custom_template(user_id=user_id, template=template)

        embed = discord.Embed(
            title="📝テンプレートを保存しました",
            description=f"タイトル: **{template.title}**",
            color=discord.Color.green(),
        )

        context.update_context(
            state=AmidakujiState.TEMPLATE_DETERMINED,
            result=template,
            interaction=context.interaction,
        )

        return [
            DeferResponseAction(ephemeral=True),
            SendMessageAction(embed=embed, ephemeral=True, followup=True),
        ]


class UseHistoryHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        current_user = context.interaction.user
        db_manager = resolve_db_manager(context, services)
        user_data = db_manager.get_user(current_user.id)
        user_least_template = getattr(user_data, "least_template", None) if user_data else None

        if not user_least_template:
            embed = discord.Embed(
                title="エラーが発生しました🥲",
                description="履歴が見つかりませんでした。",
                color=discord.Color.red(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title=user_least_template.title,
            description="このテンプレートを使用します。",
        )

        first_interaction = context.history.get(AmidakujiState.COMMAND_EXECUTED)
        if not isinstance(first_interaction, discord.Interaction):
            raise ValueError("Initial interaction is not available")

        context.update_context(
            state=AmidakujiState.TEMPLATE_DETERMINED,
            result=user_least_template,
            interaction=context.interaction,
        )

        return SendMessageAction(
            embed=embed,
            ephemeral=True,
            followup=True,
            interaction=first_interaction,
        )


class TemplateDeterminedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        user_id = context.interaction.user.id
        db_manager = resolve_db_manager(context, services)
        db_manager.set_least_template(user_id, template)

        view = MemberSelectView(context=context)
        return SendViewAction(view=view)


class MemberSelectedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        selected_members = context.result
        if not isinstance(selected_members, list):
            raise ValueError("Members are not selected")

        selected_template = context.history.get(AmidakujiState.TEMPLATE_DETERMINED)
        if not isinstance(selected_template, Template):
            raise ValueError("Template is not selected")

        choices = selected_template.choices
        pairs = data_process.create_pair_from_list(selected_members, choices)
        db_manager = resolve_db_manager(context, services)
        embeds = data_process.create_embeds_from_pairs(
            pairs=pairs, mode=db_manager.get_embed_mode()
        )

        return SendMessageAction(embeds=embeds, ephemeral=False)


class CancelledHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction] | None:
        return None
