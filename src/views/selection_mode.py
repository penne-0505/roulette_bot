from __future__ import annotations

import discord

from db_manager import DBManager
from domain import SelectionMode


def _mode_label(mode: SelectionMode) -> str:
    mapping = {
        SelectionMode.RANDOM: "完全ランダム",
        SelectionMode.BIAS_REDUCTION: "偏り軽減",
    }
    return mapping.get(mode, mode.value)


def create_selection_mode_overview_embed(mode: SelectionMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="現在の抽選モード",
        description=f"現在のモード: **{label}**",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="ボタンで変更するか、キャンセルできます。")
    return embed


def create_selection_mode_changed_embed(mode: SelectionMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="抽選モードを変更しました",
        description=f"現在のモード: **{label}**",
        color=discord.Color.green(),
    )
    return embed


def create_selection_mode_cancelled_embed(mode: SelectionMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="抽選モードの変更をキャンセルしました",
        description=f"現在のモード: **{label}**",
        color=discord.Color.light_grey(),
    )
    return embed


class SelectionModeView(discord.ui.View):
    def __init__(self, *, db_manager: DBManager, current_mode: SelectionMode, user_id: int):
        super().__init__(timeout=180)
        self.db_manager = db_manager
        self.current_mode = current_mode
        self.user_id = user_id

        self.add_item(_SelectionModeChangeButton())
        self.add_item(_SelectionModeCancelButton())

    def disable_all_items(self) -> None:
        disable_all = getattr(super(), "disable_all_items", None)
        if callable(disable_all):
            disable_all()
            return
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "この操作はコマンドを実行したユーザーだけが利用できます。",
                ephemeral=True,
            )
            return False
        return True

    def _toggle_mode(self) -> SelectionMode:
        if self.current_mode is SelectionMode.RANDOM:
            return SelectionMode.BIAS_REDUCTION
        return SelectionMode.RANDOM

    async def on_timeout(self) -> None:  # pragma: no cover - Discord依存
        self.disable_all_items()


class _SelectionModeChangeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="変更する", style=discord.ButtonStyle.primary)

    def _selection_view(self) -> SelectionModeView:
        view = self.view
        if not isinstance(view, SelectionModeView):
            raise RuntimeError("Unexpected view type attached to SelectionModeChangeButton")
        return view

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self._selection_view()
        new_mode = view._toggle_mode()
        view.db_manager.set_selection_mode(new_mode)
        view.current_mode = new_mode
        view.disable_all_items()
        view.stop()
        await interaction.response.edit_message(
            embed=create_selection_mode_changed_embed(new_mode),
            view=view,
        )


class _SelectionModeCancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="キャンセル", style=discord.ButtonStyle.secondary)

    def _selection_view(self) -> SelectionModeView:
        view = self.view
        if not isinstance(view, SelectionModeView):
            raise RuntimeError("Unexpected view type attached to SelectionModeCancelButton")
        return view

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self._selection_view()
        view.disable_all_items()
        view.stop()
        await interaction.response.edit_message(
            embed=create_selection_mode_cancelled_embed(view.current_mode),
            view=None,
        )
