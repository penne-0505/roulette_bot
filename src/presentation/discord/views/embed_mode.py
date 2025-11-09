from __future__ import annotations

import discord

from application.services.history_service import HistoryApplicationService
from domain import ResultEmbedMode
from presentation.discord.components.embeds import (
    create_embed_mode_cancelled_embed,
    create_embed_mode_changed_embed,
)
from presentation.discord.views.state import EmbedModeState


class EmbedModeView(discord.ui.View):
    def __init__(
        self,
        *,
        state: EmbedModeState,
        history_service: HistoryApplicationService,
    ) -> None:
        super().__init__(timeout=180)
        self._history_service = history_service
        self.state = state

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
        if interaction.user.id != self.state.user_id:
            await interaction.response.send_message(
                "この操作はコマンドを実行したユーザーだけが利用できます。",
                ephemeral=True,
            )
            return False
        return True

    def _toggle_mode(self) -> ResultEmbedMode:
        if self.state.current_mode is ResultEmbedMode.COMPACT:
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
        view._history_service.set_embed_mode(new_mode)
        view.state = EmbedModeState(current_mode=new_mode, user_id=view.state.user_id)
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
            embed=create_embed_mode_cancelled_embed(view.state.current_mode),
            view=view,
        )
