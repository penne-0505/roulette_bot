from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import discord

import data_process
from flow.actions import FlowAction, SendMessageAction
from flow.handlers.base import BaseStateHandler, resolve_db_manager
from models.context_model import CommandContext
from models.model import AssignmentHistory, PairList, SelectionMode, Template
from models.state_model import AmidakujiState


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
        cls,
        histories: list[AssignmentHistory],
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
        self,
        context: CommandContext,
        services: Any,
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
                members=selected_members,
                choices=choices,
                streaks=streaks_before,
            )

        pairs = data_process.create_pair_from_list(
            selected_members,
            choices,
            selection_mode=selection_mode,
            weights=weights,
        )

        embeds = data_process.create_embeds_from_pairs(
            pairs=pairs,
            mode=db_manager.get_embed_mode(),
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
            embeds=embeds,
            ephemeral=False,
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
                "以下のメンバーが同じ役割を連続して担当しています。\n"
                "必要に応じて `/amidakuji` を再実行してください。\n\n"
                f"{warning_text}"
            ),
            color=discord.Color.orange(),
        )

        return [
            primary_action,
            SendMessageAction(embed=warning_embed, ephemeral=True),
        ]


__all__ = ["MemberSelectedHandler"]
