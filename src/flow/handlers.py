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
from models.model import Template, TemplateScope
from models.state_model import AmidakujiState
from views.view import (
    ApplyOptionsView,
    DeleteTemplateView,
    EnterOptionView,
    MemberSelectView,
    PublicTemplateSelectView,
    SelectTemplateView,
    SharedTemplateActionView,
    SharedTemplateSelectView,
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
        guild_id = getattr(context.interaction, "guild_id", None)
        user_data = db_manager.get_user(target_user.id, guild_id=guild_id)
        templates = [
            template
            for template in (user_data.custom_templates if user_data else [])
            if template.scope is TemplateScope.PRIVATE
        ]

        if not templates:
            embed = discord.Embed(
                title="テンプレートが見つかりません",
                description="まずはテンプレートを作成するか、共有テンプレートを利用してください。",
                color=discord.Color.orange(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        view = SelectTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class DeleteTemplateModeHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        target_user = context.interaction.user
        db_manager = resolve_db_manager(context, services)
        guild_id = getattr(context.interaction, "guild_id", None)
        user_data = db_manager.get_user(target_user.id, guild_id=guild_id)
        templates = [
            template
            for template in (user_data.custom_templates if user_data else [])
            if template.scope is TemplateScope.PRIVATE
        ]

        if not templates:
            embed = discord.Embed(
                title="エラーが発生しました🥲",
                description="削除できるテンプレートが見つかりませんでした。",
                color=discord.Color.red(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        view = DeleteTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class UseSharedTemplatesHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        target_user = context.interaction.user
        guild_id = getattr(context.interaction, "guild_id", None)
        if guild_id is None:
            embed = discord.Embed(
                title="共有テンプレートは利用できません",
                description="サーバー内でのみ共有テンプレートを利用できます。",
                color=discord.Color.red(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        db_manager = resolve_db_manager(context, services)
        user_data = db_manager.get_user(target_user.id, guild_id=guild_id)
        templates = user_data.shared_templates if user_data else []

        if not templates:
            embed = discord.Embed(
                title="共有テンプレートが見つかりません",
                description="共有テンプレートが登録されていません。管理者に作成を依頼してください。",
                color=discord.Color.orange(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        view = SharedTemplateSelectView(context=context, templates=templates)
        return SendViewAction(view=view)


class UsePublicTemplatesHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        target_user = context.interaction.user
        guild_id = getattr(context.interaction, "guild_id", None)
        db_manager = resolve_db_manager(context, services)
        user_data = db_manager.get_user(target_user.id, guild_id=guild_id)
        templates = user_data.public_templates if user_data else []

        if not templates:
            embed = discord.Embed(
                title="公開テンプレートが見つかりません",
                description="利用可能な公開テンプレートがありません。",
                color=discord.Color.orange(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        view = PublicTemplateSelectView(context=context, templates=templates)
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


class SharedTemplateSelectedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        scope_label = (
            "共有"
            if template.scope is TemplateScope.GUILD
            else "公開"
        )
        embed = discord.Embed(
            title=f"{template.title}",
            description=f"{scope_label}テンプレートを利用するか、自分用にコピーできます。",
            color=discord.Color.blurple(),
        )
        if template.choices:
            embed.add_field(
                name="候補",
                value="\n".join(f"・{choice}" for choice in template.choices),
                inline=False,
            )

        view = SharedTemplateActionView(context=context, template=template)
        return SendViewAction(view=view, followup=True)


class SharedTemplateCopyHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        db_manager = resolve_db_manager(context, services)
        user_id = context.interaction.user.id
        copied_template = db_manager.copy_shared_template_to_user(user_id, template)

        embed = discord.Embed(
            title="共有テンプレートをコピーしました",
            description=f"**{copied_template.title}** を自分のテンプレートに追加しました。",
            color=discord.Color.green(),
        )

        return SendMessageAction(embed=embed, ephemeral=True, followup=True)


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


class TemplateDeletedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        template_title = context.result
        if not isinstance(template_title, str):
            raise ValueError("Template title must be a string")

        user_id = context.interaction.user.id
        db_manager = resolve_db_manager(context, services)
        db_manager.delete_custom_template(
            user_id=user_id, template_title=template_title
        )

        embed = discord.Embed(
            title="🗑️テンプレートを削除しました",
            description=f"タイトル: **{template_title}**",
            color=discord.Color.orange(),
        )

        current_interaction = context.interaction
        context.update_context(
            state=AmidakujiState.MODE_USE_EXISTING,
            result=current_interaction,
            interaction=current_interaction,
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
        guild_id = getattr(context.interaction, "guild_id", None)
        user_data = db_manager.get_user(current_user.id, guild_id=guild_id)
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
