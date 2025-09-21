from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import discord

from components.modal import TitleEnterModal
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
    filter_private_templates,
    resolve_db_manager,
    resolve_user_context,
)
from models.context_model import CommandContext
from models.model import Template, TemplateScope
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
        user_context = resolve_user_context(context, services)
        templates = filter_private_templates(user_context.user_data)

        if not templates:
            return build_ephemeral_embed_action(
                title="テンプレートが見つかりません",
                description=(
                    "まずは `/amidakuji_template_create` でテンプレートを作成するか、"
                    "共有テンプレートを利用してください。"
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
        user_context = resolve_user_context(context, services)
        templates = filter_private_templates(user_context.user_data)

        if not templates:
            return build_ephemeral_embed_action(
                title="エラーが発生しました🥲",
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
        user_context = resolve_user_context(context, services)

        if user_context.guild_id is None:
            return build_ephemeral_embed_action(
                title="共有テンプレートは利用できません",
                description="サーバー内でのみ共有テンプレートを利用できます。",
                color=discord.Color.red(),
            )

        templates = (
            user_context.user_data.shared_templates if user_context.user_data else []
        )

        if not templates:
            return build_ephemeral_embed_action(
                title="共有テンプレートが見つかりません",
                description="共有テンプレートが登録されていません。管理者に作成を依頼してください。",
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
        user_context = resolve_user_context(context, services)
        templates = (
            user_context.user_data.public_templates if user_context.user_data else []
        )

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
        db_manager = resolve_db_manager(context, services)
        db_manager.add_custom_template(user_id=user_id, template=template)

        embed = discord.Embed(
            title="📝テンプレートを保存しました",
            description=f"タイトル: **{template.title}**",
            color=discord.Color.green(),
        )

        is_main_flow = AmidakujiState.COMMAND_EXECUTED in context.history

        actions: list[FlowAction] = [
            DeferResponseAction(ephemeral=True),
            SendMessageAction(embed=embed, ephemeral=True, followup=True),
        ]

        if is_main_flow:
            context.update_context(
                state=AmidakujiState.TEMPLATE_DETERMINED,
                result=template,
                interaction=context.interaction,
            )

        return actions


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
        db_manager = resolve_db_manager(context, services)
        db_manager.delete_custom_template(
            user_id=user_id,
            template_title=template_title,
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
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        user_context = resolve_user_context(context, services)
        user_least_template = (
            getattr(user_context.user_data, "least_template", None)
            if user_context.user_data
            else None
        )

        if not user_least_template:
            return build_ephemeral_embed_action(
                title="エラーが発生しました🥲",
                description="履歴が見つかりませんでした。",
                color=discord.Color.red(),
            )

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
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        template = context.result
        if not isinstance(template, Template):
            raise ValueError("Template is not selected")

        user_id = context.interaction.user.id
        db_manager = resolve_db_manager(context, services)
        db_manager.set_least_template(user_id, template)

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
