"""Actions representing Discord responses triggered by state handlers."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol, Sequence

import discord

from models.context_model import CommandContext


class FlowAction(Protocol):
    """Protocol for actions executed by the flow controller."""

    async def execute(self, context: CommandContext) -> None:
        """Execute the action for the given command context."""


@dataclass(slots=True)
class _BaseAction:
    interaction: discord.Interaction | None = None

    def _resolve_interaction(self, context: CommandContext) -> discord.Interaction:
        if self.interaction is not None:
            return self.interaction
        return context.interaction


@dataclass(slots=True)
class SendViewAction(_BaseAction):
    """Send a Discord view either via initial response or a follow-up."""

    view: discord.ui.View | None = None
    ephemeral: bool = True
    followup: bool | None = None

    async def execute(self, context: CommandContext) -> None:
        interaction = self._resolve_interaction(context)
        view = self.view
        if view is None:
            return

        use_followup = self.followup
        if use_followup is None:
            use_followup = interaction.response.is_done()

        if use_followup:
            await interaction.followup.send(view=view, ephemeral=self.ephemeral)
        else:
            await interaction.response.send_message(view=view, ephemeral=self.ephemeral)


@dataclass(slots=True)
class ShowModalAction(_BaseAction):
    """Show a modal to the user."""

    modal: discord.ui.Modal | None = None

    async def execute(self, context: CommandContext) -> None:
        interaction = self._resolve_interaction(context)
        modal = self.modal
        if modal is None:
            return
        await interaction.response.send_modal(modal)


@dataclass(slots=True)
class SendMessageAction(_BaseAction):
    """Send a Discord message using the current interaction."""

    content: str | None = None
    embed: discord.Embed | None = None
    embeds: Sequence[discord.Embed] | None = None
    ephemeral: bool = True
    followup: bool | None = None
    view: discord.ui.View | None = None
    delete_after: float | None = None

    async def execute(self, context: CommandContext) -> None:
        interaction = self._resolve_interaction(context)
        use_followup = self.followup
        if use_followup is None:
            use_followup = interaction.response.is_done()

        payload: dict[str, object | None] = {"content": self.content}
        if self.embed is not None:
            payload["embed"] = self.embed
        if self.embeds is not None:
            payload["embeds"] = list(self.embeds)
        if self.view is not None:
            payload["view"] = self.view

        message: discord.Message | None = None
        if use_followup:
            message = await interaction.followup.send(
                ephemeral=self.ephemeral,
                **payload,
            )
        else:
            await interaction.response.send_message(ephemeral=self.ephemeral, **payload)
            if self.delete_after is not None:
                try:
                    message = await interaction.original_response()
                except (discord.HTTPException, discord.NotFound):
                    message = None

        if self.delete_after is not None and message is not None:
            asyncio.create_task(self._schedule_delete(message, self.delete_after))

    @staticmethod
    async def _schedule_delete(
        message: discord.Message, delay: float
    ) -> None:
        try:
            await asyncio.sleep(delay)
            await message.delete()
        except (discord.HTTPException, discord.NotFound):
            pass


@dataclass(slots=True)
class DeferResponseAction(_BaseAction):
    """Defer the current interaction response if it has not been responded."""

    ephemeral: bool = True

    async def execute(self, context: CommandContext) -> None:
        interaction = self._resolve_interaction(context)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=self.ephemeral)


@dataclass(slots=True)
class EditMessageAction(_BaseAction):
    """Edit the original interaction message with updated content."""

    content: str | None = None
    embed: discord.Embed | None = None
    embeds: Sequence[discord.Embed] | None = None
    view: discord.ui.View | None = None

    async def execute(self, context: CommandContext) -> None:
        interaction = self._resolve_interaction(context)
        payload: dict[str, object | None] = {"content": self.content}
        if self.embed is not None:
            payload["embed"] = self.embed
        if self.embeds is not None:
            payload["embeds"] = list(self.embeds)
        if self.view is not None:
            payload["view"] = self.view

        if interaction.response.is_done():
            await interaction.edit_original_response(**payload)
        else:
            await interaction.response.edit_message(**payload)
