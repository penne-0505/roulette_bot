from __future__ import annotations

import discord


class DisableViewOnCallbackMixin:
    """Mixin that disables view items after a successful callback."""

    disable_on_success: bool = False
    disable_entire_view: bool = True

    def _should_disable_after_dispatch(self) -> bool:
        return self.disable_on_success

    def _disable_items(self, view: discord.ui.View) -> None:
        if self.disable_entire_view:
            disable_all = getattr(view, "disable_all_items", None)
            if callable(disable_all):
                disable_all()
                return
            for item in list(view.children):
                item.disabled = True
        else:
            for item in list(view.children):
                if item is self:
                    item.disabled = True

    async def _commit_disabled_view(
        self, interaction: discord.Interaction, view: discord.ui.View
    ) -> None:
        message = getattr(interaction, "message", None)
        try:
            if message is not None:
                await message.edit(view=view)
            elif interaction.response.is_done():
                await interaction.edit_original_response(view=view)
            else:
                await interaction.response.edit_message(view=view)
        except (discord.HTTPException, discord.NotFound, discord.Forbidden):
            pass

    async def _cleanup_after_callback(self, interaction: discord.Interaction) -> None:
        if not self._should_disable_after_dispatch():
            return
        view = getattr(self, "view", None)
        if not isinstance(view, discord.ui.View):
            return
        self._disable_items(view)
        await self._commit_disabled_view(interaction, view)
