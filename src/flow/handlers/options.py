from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import discord

from components.modal import OptionNameEnterModal
from flow.actions import (
    EditMessageAction,
    FlowAction,
    SendMessageAction,
    SendViewAction,
    ShowModalAction,
)
from flow.handlers.base import BaseStateHandler
from models.context_model import CommandContext
from views.view import ApplyOptionsView, EnterOptionView


def _build_options_embed(
    options: Sequence[str],
    selected_index: int | None,
) -> discord.Embed:
    if options:
        lines: list[str] = []
        for index, option in enumerate(options, start=1):
            label = discord.utils.escape_markdown(option)
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


class EnterOptionButtonHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        modal = OptionNameEnterModal(context=context)
        return ShowModalAction(modal=modal)


class OptionNameEnteredHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        if not isinstance(context.result, list):
            raise TypeError("Options must be a list of strings")

        context.set_option_snapshot(context.result, select_last=True)
        embed = _build_options_embed(
            context.options_snapshot,
            context.option_edit_index,
        )
        view = ApplyOptionsView(context=context)
        return SendMessageAction(embed=embed, view=view, ephemeral=True)


class NeedMoreOptionsHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
    ) -> FlowAction | Sequence[FlowAction]:
        modal = OptionNameEnterModal(context=context)
        return ShowModalAction(modal=modal)


class OptionSelectionChangedHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
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
        self,
        context: CommandContext,
        services: Any,
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
            context.options_snapshot,
            context.option_edit_index,
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
        self,
        context: CommandContext,
        services: Any,
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
            context.options_snapshot,
            context.option_edit_index,
        )
        view = ApplyOptionsView(context=context)
        message = SendMessageAction(
            content=f"「{moved_option}」を上に移動しました。",
            ephemeral=True,
            followup=True,
            delete_after=5.0,
        )
        return [EditMessageAction(embed=embed, view=view), message]


class OptionMovedDownHandler(BaseStateHandler):
    async def handle(
        self,
        context: CommandContext,
        services: Any,
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
            context.options_snapshot,
            context.option_edit_index,
        )
        view = ApplyOptionsView(context=context)
        message = SendMessageAction(
            content=f"「{moved_option}」を下に移動しました。",
            ephemeral=True,
            followup=True,
            delete_after=5.0,
        )
        return [EditMessageAction(embed=embed, view=view), message]


__all__ = [
    "EnterOptionButtonHandler",
    "NeedMoreOptionsHandler",
    "OptionDeletedHandler",
    "OptionMovedDownHandler",
    "OptionMovedUpHandler",
    "OptionNameEnteredHandler",
    "OptionSelectionChangedHandler",
]
