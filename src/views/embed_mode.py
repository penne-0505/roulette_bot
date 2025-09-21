from __future__ import annotations

import discord

from db_manager import DBManager
from models.model import ResultEmbedMode


def _mode_label(mode: ResultEmbedMode) -> str:
    mapping = {
        ResultEmbedMode.COMPACT: "コンパクト",
        ResultEmbedMode.DETAILED: "詳細",
    }
    return mapping.get(mode, mode.value)


def create_embed_mode_overview_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="現在の埋め込み表示形式",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="ボタンで変更するか、キャンセルできます。")
    return embed


def create_embed_mode_changed_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="埋め込み表示形式を変更しました",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.green(),
    )
    return embed


def create_embed_mode_cancelled_embed(mode: ResultEmbedMode) -> discord.Embed:
    label = _mode_label(mode)
    embed = discord.Embed(
        title="埋め込み表示形式の変更をキャンセルしました",
        description=f"現在の表示形式: **{label}**",
        color=discord.Color.light_grey(),
    )
    return embed


class EmbedModeView(discord.ui.View):
    def __init__(
        self,
        *,
        db_manager: DBManager,
        current_mode: ResultEmbedMode,
        user_id: int,
    ) -> None:
        super().__init__(timeout=180)
        self.db_manager = db_manager
        self.current_mode = current_mode
        self.user_id = user_id

        self.add_item(_EmbedModeChangeButton())
        self.add_item(_EmbedModeCancelButton())

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

    def _toggle_mode(self) -> ResultEmbedMode:
        if self.current_mode is ResultEmbedMode.COMPACT:
            return ResultEmbedMode.DETAILED
        return ResultEmbedMode.COMPACT

    async def on_timeout(self) -> None:  # pragma: no cover - Discord依存
        self.disable_all_items()


class _EmbedModeChangeButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="変更する", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, EmbedModeView)
        new_mode = view._toggle_mode()
        view.db_manager.set_embed_mode(new_mode)
        view.current_mode = new_mode
        view.disable_all_items()
        view.stop()
        await interaction.response.edit_message(
            embed=create_embed_mode_changed_embed(new_mode),
            view=view,
        )


class _EmbedModeCancelButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(label="キャンセル", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, EmbedModeView)
        view.disable_all_items()
        view.stop()
        await interaction.response.edit_message(
            embed=create_embed_mode_cancelled_embed(view.current_mode),
            view=view,
        )
