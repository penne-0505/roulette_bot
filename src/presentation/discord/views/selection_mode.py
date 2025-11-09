from __future__ import annotations

import discord

from application.services.history_service import HistoryApplicationService
from domain import SelectionMode
from presentation.discord.components.embeds import (
    create_selection_mode_cancelled_embed,
    create_selection_mode_changed_embed,
)
from presentation.discord.views.state import SelectionModeState


class SelectionModeView(discord.ui.View):
    def __init__(
        self,
        *,
        state: SelectionModeState,
        history_service: HistoryApplicationService,
    ) -> None:
        super().__init__(timeout=180)
        self._history_service = history_service
        self.state = state

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
        if interaction.user.id != self.state.user_id:
            await interaction.response.send_message(
                "この操作はコマンドを実行したユーザーだけが利用できます。",
                ephemeral=True,
            )
            return False
        return True

    def _toggle_mode(self) -> SelectionMode:
        if self.state.current_mode is SelectionMode.RANDOM:
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
        view._history_service.set_selection_mode(new_mode)
        view.state = SelectionModeState(current_mode=new_mode, user_id=view.state.user_id)
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
            embed=create_selection_mode_cancelled_embed(view.state.current_mode),
            view=None,
        )
