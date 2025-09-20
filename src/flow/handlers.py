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
from models.model import AssignmentHistory, PairList, SelectionMode, Template
from models.state_model import AmidakujiState
from views.view import (
    ApplyOptionsView,
    DeleteTemplateView,
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
