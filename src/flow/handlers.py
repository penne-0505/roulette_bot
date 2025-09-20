"""State handlers that produce flow actions for Amidakuji interactions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, NamedTuple

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
from models.model import (
    AssignmentHistory,
    PairList,
    SelectionMode,
    Template,
    TemplateScope,
    UserInfo,
)
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


class _UserContext(NamedTuple):
    db_manager: "DBManager"
    user_data: UserInfo | None
    guild_id: int | None


def _resolve_user_context(
    context: CommandContext, services: Any
) -> _UserContext:
    db_manager = resolve_db_manager(context, services)
    interaction = context.interaction
    guild_id = getattr(interaction, "guild_id", None)
    user_id = getattr(interaction.user, "id", None)
    user_data = db_manager.get_user(user_id, guild_id=guild_id) if user_id else None
    return _UserContext(db_manager=db_manager, user_data=user_data, guild_id=guild_id)


def _build_ephemeral_embed_action(
    *, title: str, description: str, color: discord.Color
) -> SendMessageAction:
    embed = discord.Embed(title=title, description=description, color=color)
    return SendMessageAction(embed=embed, ephemeral=True)


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
        user_context = _resolve_user_context(context, services)
        templates = [
            template
            for template in (user_context.user_data.custom_templates if user_context.user_data else [])
            if template.scope is TemplateScope.PRIVATE
        ]

        if not templates:
            return _build_ephemeral_embed_action(
                title="テンプレートが見つかりません",
                description="まずはテンプレートを作成するか、共有テンプレートを利用してください。",
                color=discord.Color.orange(),
            )

        view = SelectTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class DeleteTemplateModeHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        user_context = _resolve_user_context(context, services)
        templates = [
            template
            for template in (user_context.user_data.custom_templates if user_context.user_data else [])
            if template.scope is TemplateScope.PRIVATE
        ]

        if not templates:
            return _build_ephemeral_embed_action(
                title="エラーが発生しました🥲",
                description="削除できるテンプレートが見つかりませんでした。",
                color=discord.Color.red(),
            )

        view = DeleteTemplateView(context=context, templates=templates)
        return SendViewAction(view=view)


class UseSharedTemplatesHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        user_context = _resolve_user_context(context, services)

        if user_context.guild_id is None:
            return _build_ephemeral_embed_action(
                title="共有テンプレートは利用できません",
                description="サーバー内でのみ共有テンプレートを利用できます。",
                color=discord.Color.red(),
            )

        templates = (
            user_context.user_data.shared_templates
            if user_context.user_data
            else []
        )

        if not templates:
            return _build_ephemeral_embed_action(
                title="共有テンプレートが見つかりません",
                description="共有テンプレートが登録されていません。管理者に作成を依頼してください。",
                color=discord.Color.orange(),
            )

        view = SharedTemplateSelectView(context=context, templates=templates)
        return SendViewAction(view=view)


class UsePublicTemplatesHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction]:
        user_context = _resolve_user_context(context, services)
        templates = (
            user_context.user_data.public_templates
            if user_context.user_data
            else []
        )

        if not templates:
            return _build_ephemeral_embed_action(
                title="公開テンプレートが見つかりません",
                description="利用可能な公開テンプレートがありません。",
                color=discord.Color.orange(),
            )

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
        user_context = _resolve_user_context(context, services)
        user_least_template = (
            getattr(user_context.user_data, "least_template", None)
            if user_context.user_data
            else None
        )

        if not user_least_template:
            return _build_ephemeral_embed_action(
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
    HISTORY_LOOKBACK = 10
    CONSECUTIVE_THRESHOLD = 3

    @staticmethod
    def _normalize_selection_mode(mode: str | SelectionMode) -> SelectionMode:
        if isinstance(mode, SelectionMode):
            return mode
        try:
            return SelectionMode(str(mode))
        except ValueError:
            return SelectionMode.RANDOM

    @classmethod
    def _build_streaks(
        cls, histories: list[AssignmentHistory]
    ) -> dict[int, tuple[str | None, int]]:
        streaks: dict[int, tuple[str | None, int]] = {}
        for history in sorted(histories, key=lambda item: item.created_at):
            for entry in history.entries:
                last_choice, count = streaks.get(entry.user_id, (None, 0))
                if entry.choice == last_choice:
                    streaks[entry.user_id] = (entry.choice, count + 1)
                else:
                    streaks[entry.user_id] = (entry.choice, 1)
        return streaks

    @classmethod
    def _build_weight_map(
        cls,
        *,
        members: list[discord.User],
        choices: list[str],
        streaks: dict[int, tuple[str | None, int]],
    ) -> dict[int, dict[str, float]]:
        weight_map: dict[int, dict[str, float]] = {}
        for member in members:
            last_choice, count = streaks.get(member.id, (None, 0))
            member_weights: dict[str, float] = {}
            for choice in choices:
                if choice == last_choice and count > 0:
                    member_weights[choice] = 1.0 / (count + 1)
                else:
                    member_weights[choice] = 1.0
            weight_map[member.id] = member_weights
        return weight_map

    @classmethod
    def _update_streaks_with_pairs(
        cls,
        streaks: dict[int, tuple[str | None, int]],
        pairs: PairList,
    ) -> dict[int, tuple[str | None, int]]:
        updated = dict(streaks)
        for pair in pairs.pairs:
            last_choice, count = updated.get(pair.user.id, (None, 0))
            if pair.choice == last_choice:
                updated[pair.user.id] = (pair.choice, count + 1)
            else:
                updated[pair.user.id] = (pair.choice, 1)
        return updated

    @classmethod
    def _detect_bias(
        cls,
        streaks: dict[int, tuple[str | None, int]],
        *,
        threshold: int,
        members: list[discord.User],
    ) -> list[tuple[str, str, int]]:
        member_map = {member.id: member for member in members}
        warnings: list[tuple[str, str, int]] = []
        for user_id, (choice, count) in streaks.items():
            if choice is None:
                continue
            if count > threshold:
                member = member_map.get(user_id)
                display_name = getattr(member, "display_name", str(user_id))
                warnings.append((display_name, choice, count))
        return warnings

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
        db_manager = resolve_db_manager(context, services)
        selection_mode_value = db_manager.get_selection_mode()
        selection_mode = self._normalize_selection_mode(selection_mode_value)

        current_guild = context.interaction.guild
        guild_id = getattr(current_guild, "id", None) or getattr(
            context.interaction, "guild_id", 0
        )

        history_records = db_manager.get_recent_history(
            guild_id=guild_id,
            template_title=selected_template.title,
            limit=self.HISTORY_LOOKBACK,
        )
        streaks_before = self._build_streaks(history_records)
        weights = None
        if selection_mode is SelectionMode.BIAS_REDUCTION:
            weights = self._build_weight_map(
                members=selected_members, choices=choices, streaks=streaks_before
            )

        pairs = data_process.create_pair_from_list(
            selected_members,
            choices,
            selection_mode=selection_mode,
            weights=weights,
        )

        embeds = data_process.create_embeds_from_pairs(
            pairs=pairs, mode=db_manager.get_embed_mode()
        )

        db_manager.save_history(
            guild_id=guild_id,
            template=selected_template,
            pairs=pairs,
            selection_mode=selection_mode,
        )

        updated_streaks = self._update_streaks_with_pairs(streaks_before, pairs)
        warnings = self._detect_bias(
            updated_streaks,
            threshold=self.CONSECUTIVE_THRESHOLD,
            members=selected_members,
        )

        primary_action: FlowAction = SendMessageAction(
            embeds=embeds, ephemeral=False
        )

        if not warnings:
            return primary_action

        warning_lines = [
            f"• {name} は {choice} を {count} 回連続で担当しています"
            for name, choice, count in warnings
        ]
        warning_text = "\n".join(warning_lines)
        warning_embed = discord.Embed(
            title="⚠️ 偏りを検知しました",
            description=(
                f"以下のメンバーが同じ役割を連続して担当しています。\n"
                f"必要に応じて `/amidakuji` を再実行してください。\n\n{warning_text}"
            ),
            color=discord.Color.orange(),
        )

        return [
            primary_action,
            SendMessageAction(embed=warning_embed, ephemeral=True),
        ]


class CancelledHandler(BaseStateHandler):
    async def handle(
        self, context: CommandContext, services: Any
    ) -> FlowAction | Sequence[FlowAction] | None:
        return None
