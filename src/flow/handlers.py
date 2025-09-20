"""State handlers that produce flow actions for Amidakuji interactions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import discord

import data_process
from flow.actions import (
    DeferResponseAction,
    EditMessageAction,
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
    DeleteTemplateView,
    EnterOptionView,
    MemberSelectView,
    SelectTemplateView,
)
from components.modal import OptionNameEnterModal, TitleEnterModal
from discord.utils import escape_markdown

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


def _build_options_embed(
    options: Sequence[str], selected_index: int | None
) -> discord.Embed:
    if options:
        lines: list[str] = []
        for index, option in enumerate(options, start=1):
            label = escape_markdown(option)
            if index - 1 == selected_index:
                label = f"**{label}**"
            lines.append(f"{index}. {label}")
        description = "\n".join(lines)
    else:
        description = "まだオプションが登録されていません。"

    return discord.Embed(
        title="現在の選択肢",
        description=description,
        color=discord.Color.blurple(),
    )


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


class DeleteTemplateModeHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        target_user = context.interaction.user
        db_manager = resolve_db_manager(context, services)
        user_data = db_manager.get_user(target_user.id)
        templates = user_data.custom_templates if user_data else []

        if not templates:
            embed = discord.Embed(
                title="エラーが発生しました🥲",
                description="削除できるテンプレートが見つかりませんでした。",
                color=discord.Color.red(),
            )
            return SendMessageAction(embed=embed, ephemeral=True)

        view = DeleteTemplateView(context=context, templates=templates)
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
        if not isinstance(context.result, list):
            raise TypeError("Options must be a list of strings")

        context.set_option_snapshot(context.result, select_last=True)
        embed = _build_options_embed(
            context.options_snapshot, context.option_edit_index
        )
        view = ApplyOptionsView(context=context)
        return SendMessageAction(embed=embed, view=view, ephemeral=True)


class NeedMoreOptionsHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        modal = OptionNameEnterModal(context=context)
        return ShowModalAction(modal=modal)


class OptionSelectionChangedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        if not isinstance(context.result, int):
            raise TypeError("Selection index must be an integer")

        options = context.options_snapshot
        if not options:
            return SendMessageAction(
                content="編集できるオプションがありません。先に追加してください。",
                ephemeral=True,
            )

        index = max(0, min(context.result, len(options) - 1))
        context.option_edit_index = index
        embed = _build_options_embed(options, index)
        view = ApplyOptionsView(context=context)
        return EditMessageAction(embed=embed, view=view)


class OptionDeletedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        options = list(context.options_snapshot)
        index = context.option_edit_index

        if index is None or not options:
            return SendMessageAction(
                content="削除するオプションを選択してください。",
                ephemeral=True,
            )

        if not (0 <= index < len(options)):
            return SendMessageAction(
                content="選択中のオプションを取得できませんでした。",
                ephemeral=True,
            )

        removed_option = options.pop(index)
        context.set_option_snapshot(options, preferred_index=index)

        embed = _build_options_embed(
            context.options_snapshot, context.option_edit_index
        )
        view = ApplyOptionsView(context=context)

        confirmation = SendMessageAction(
            content=f"「{removed_option}」を削除しました。",
            ephemeral=True,
            followup=True,
        )
        return [EditMessageAction(embed=embed, view=view), confirmation]


class OptionMovedUpHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        options = list(context.options_snapshot)
        index = context.option_edit_index

        if index is None or not options:
            return SendMessageAction(
                content="移動するオプションを選択してください。",
                ephemeral=True,
            )

        if index <= 0:
            return SendMessageAction(
                content="これ以上上に移動できません。",
                ephemeral=True,
            )

        options[index - 1], options[index] = options[index], options[index - 1]
        moved_option = options[index - 1]
        new_index = index - 1
        context.option_edit_index = new_index
        context.set_option_snapshot(options, preferred_index=new_index)

        embed = _build_options_embed(
            context.options_snapshot, context.option_edit_index
        )
        view = ApplyOptionsView(context=context)
        message = SendMessageAction(
            content=f"「{moved_option}」を上に移動しました。",
            ephemeral=True,
            followup=True,
        )
        return [EditMessageAction(embed=embed, view=view), message]


class OptionMovedDownHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        options = list(context.options_snapshot)
        index = context.option_edit_index

        if index is None or not options:
            return SendMessageAction(
                content="移動するオプションを選択してください。",
                ephemeral=True,
            )

        if index >= len(options) - 1:
            return SendMessageAction(
                content="これ以上下に移動できません。",
                ephemeral=True,
            )

        options[index + 1], options[index] = options[index], options[index + 1]
        moved_option = options[index + 1]
        new_index = index + 1
        context.option_edit_index = new_index
        context.set_option_snapshot(options, preferred_index=new_index)

        embed = _build_options_embed(
            context.options_snapshot, context.option_edit_index
        )
        view = ApplyOptionsView(context=context)
        message = SendMessageAction(
            content=f"「{moved_option}」を下に移動しました。",
            ephemeral=True,
            followup=True,
        )
        return [EditMessageAction(embed=embed, view=view), message]


class TemplateCreatedHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
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
