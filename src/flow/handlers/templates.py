"""テンプレート関連ステートのハンドラ群。"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import discord

from application.dto import HistoryUsageResultDTO, TemplateCreationResultDTO
from application.services.flow_service import FlowContext
from components.modal import TitleEnterModal
from domain import Template, TemplateScope
from flow.actions import (
    DeferResponseAction,
    FlowAction,
    SendMessageAction,
    SendViewAction,
    ShowModalAction,
)
from flow.handlers.base import (
    BaseStateHandler,
    build_ephemeral_embed_action,
    resolve_flow_service,
    resolve_template_service,
)
from models.context_model import CommandContext
from models.state_model import AmidakujiState
from views.view import (
    DeleteTemplateView,
    EnterOptionView,
    MemberSelectView,
    PublicTemplateSelectView,
    SelectTemplateView,
    SharedTemplateActionView,
    SharedTemplateSelectView,
)


class UseExistingHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template_service = resolve_template_service(services)
        user_id = context.interaction.user.id
        guild_id = getattr(context.interaction, "guild_id", None)
        templates = template_service.list_private_templates(
            user_id=user_id,
            guild_id=guild_id,
        ).templates

        if not templates:
            return build_ephemeral_embed_action(
                title="テンプレートが見つかりません",
                description=(
                    "まずは `/amidakuji_template_create` でテンプレートを作成するか、"
                    "共有/公開テンプレートを利用してください。"
                ),
                color=discord.Color.orange(),
            )

        view = SelectTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class DeleteTemplateModeHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template_service = resolve_template_service(services)
        user_id = context.interaction.user.id
        guild_id = getattr(context.interaction, "guild_id", None)
        templates = template_service.list_private_templates(
            user_id=user_id,
            guild_id=guild_id,
        ).templates

        if not templates:
            return build_ephemeral_embed_action(
                title="エラーが発生しました",
                description="削除できるテンプレートが見つかりませんでした。",
                color=discord.Color.red(),
            )

        view = DeleteTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class UseSharedTemplatesHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template_service = resolve_template_service(services)
        guild_id = getattr(context.interaction, "guild_id", None)

        if guild_id is None:
            return build_ephemeral_embed_action(
                title="共有テンプレートは利用できません",
                description="サーバー内でのみ共有テンプレートを利用できます。",
                color=discord.Color.red(),
            )

        templates = template_service.list_shared_templates(guild_id=guild_id).templates

        if not templates:
            return build_ephemeral_embed_action(
                title="共有テンプレートが見つかりません",
                description="共有テンプレートが登録されていません。他のメンバーに作成・共有してもらうか、あなたが共有することもできます。",
                color=discord.Color.orange(),
            )

        view = SharedTemplateSelectView(context=context, templates=templates)
        return SendViewAction(view=view)


class UsePublicTemplatesHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template_service = resolve_template_service(services)
        templates = template_service.list_public_templates().templates

        if not templates:
            return build_ephemeral_embed_action(
                title="公開テンプレートが見つかりません",
                description="利用可能な公開テンプレートがありません。",
                color=discord.Color.orange(),
            )

        view = PublicTemplateSelectView(context=context, templates=templates)
        return SendViewAction(view=view)


class CreateNewHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        modal = TitleEnterModal(context=context)
        return ShowModalAction(modal=modal)


class TemplateTitleEnteredHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        view = EnterOptionView(context=context)
        return SendViewAction(view=view)


class SharedTemplateSelectedHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        scope_label = "共有" if template.scope is TemplateScope.GUILD else "公開"
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
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        template_service = resolve_template_service(services)
        user_id = context.interaction.user.id
        copied_template = template_service.copy_shared_template(
            user_id=user_id,
            template=template,
        ).template

        embed = discord.Embed(
            title="共有テンプレートをコピーしました",
            description=f"**{copied_template.title}** を自分のテンプレートに追加しました。",
            color=discord.Color.green(),
        )

        return SendMessageAction(embed=embed, ephemeral=True, followup=True)


class TemplateCreatedHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        if len(template.choices) < 2:
            embed = discord.Embed(
                title="オプションが不足しています",
                description="テンプレートを保存するには、2件以上のオプションが必要です。",
                color=discord.Color.orange(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        user_id = context.interaction.user.id
        flow_service = resolve_flow_service(services)
        creation_result: TemplateCreationResultDTO = flow_service.complete_template_creation(
            user_id=user_id,
            template=template,
            context=FlowContext(
                is_main_flow=AmidakujiState.COMMAND_EXECUTED in context.history
            ),
            interaction=context.interaction,
        )

        if creation_result.transition is not None:
            transition = creation_result.transition
            context.update_context(
                state=transition.next_state,
                result=transition.result,
                interaction=transition.interaction,
            )

        embed = discord.Embed(
            title="📝テンプレートを保存しました",
            description=f"タイトル: **{template.title}**",
            color=discord.Color.green(),
        )

        return [
            DeferResponseAction(ephemeral=True),
            SendMessageAction(embed=embed, ephemeral=True, followup=True),
        ]


class TemplateDeletedHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template_title = context.result
        if not isinstance(template_title, str):
            raise ValueError("Template title must be a string")

        user_id = context.interaction.user.id
        flow_service = resolve_flow_service(services)
        deletion_result = flow_service.remove_template(
            user_id=user_id,
            template_title=template_title,
            interaction=context.interaction,
        )

        transition = deletion_result.transition
        context.update_context(
            state=transition.next_state,
            result=transition.result,
            interaction=transition.interaction,
        )

        embed = discord.Embed(
            title="🗑️テンプレートを削除しました",
            description=f"タイトル: **{template_title}**",
            color=discord.Color.orange(),
        )

        return [
            DeferResponseAction(ephemeral=True),
            SendMessageAction(embed=embed, ephemeral=True, followup=True),
        ]


class UseHistoryHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        flow_service = resolve_flow_service(services)
        user_id = context.interaction.user.id
        guild_id = getattr(context.interaction, "guild_id", None)

        try:
            result: HistoryUsageResultDTO = flow_service.use_recent_template(
                user_id=user_id,
                guild_id=guild_id,
                interaction=context.interaction,
            )
        except LookupError:
            return build_ephemeral_embed_action(
                title="エラーが発生しました🥲",
                description="履歴が見つかりませんでした。",
                color=discord.Color.red(),
            )

        transition = result.transition
        context.update_context(
            state=transition.next_state,
            result=transition.result,
            interaction=transition.interaction,
        )

        embed = discord.Embed(
            title=result.template.title,
            description="このテンプレートを使用します。",
        )

        first_interaction = context.history.get(AmidakujiState.COMMAND_EXECUTED)
        if not isinstance(first_interaction, discord.Interaction):
            raise ValueError("Initial interaction is not available")

        return SendMessageAction(
            embed=embed,
            ephemeral=True,
            followup=True,
            interaction=first_interaction,
        )


class TemplateDeterminedHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        template_service = resolve_template_service(services)
        user_id = context.interaction.user.id
        template_service.mark_recent_template(user_id=user_id, template=template)

        view = MemberSelectView(context=context)
        return SendViewAction(view=view)


__all__ = [
    "CreateNewHandler",
    "DeleteTemplateModeHandler",
    "SharedTemplateCopyHandler",
    "SharedTemplateSelectedHandler",
    "TemplateCreatedHandler",
    "TemplateDeletedHandler",
    "TemplateDeterminedHandler",
    "TemplateTitleEnteredHandler",
    "UseExistingHandler",
    "UseHistoryHandler",
    "UsePublicTemplatesHandler",
    "UseSharedTemplatesHandler",
]
