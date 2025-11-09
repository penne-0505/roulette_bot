"""Flow controller that dispatches Amidakuji states to handlers."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import discord

from flow.actions import FlowAction
from flow.handlers import BaseStateHandler
from flow.registry import (
    DEFAULT_HANDLER_FACTORIES,
    FlowHandlerRegistry,
    HandlerSpec,
)
from models.context_model import CommandContext
from models.state_model import AmidakujiState


class FlowController:
    """Dispatch handlers for the current state and execute resulting actions."""

    def __init__(
        self,
        context: CommandContext,
        services: Any,
        *,
        handler_registry: FlowHandlerRegistry | None = None,
        handler_overrides: Mapping[AmidakujiState, HandlerSpec] | None = None,
    ) -> None:
        self.context = context
        self.services = services
        self._registry = handler_registry or FlowHandlerRegistry(
            default_factories=DEFAULT_HANDLER_FACTORIES,
            overrides=handler_overrides,
        )

    async def dispatch(
        self,
        state: AmidakujiState,
        result: object,
        interaction: discord.Interaction | None,
    ) -> None:
        if self.context.services is None:
            self.context.services = self.services

        self.context.update_context(state=state, result=result, interaction=interaction)
        await self._run()

    async def _run(self) -> None:
        while True:
            current_state = self.context.state
            handler = self._resolve_handler(current_state)

            actions = await handler.handle(self.context, self.services)
            await self._execute_action(actions)

            if self.context.state == current_state:
                break

    def _resolve_handler(self, state: AmidakujiState) -> BaseStateHandler:
        try:
            return self._registry.resolve(state)
        except KeyError as exc:
            raise ValueError(f"Invalid state: {state}") from exc

    async def _execute_action(
        self, action: FlowAction | Sequence[FlowAction] | None
    ) -> None:
        if action is None:
            return

        if isinstance(action, Sequence) and not hasattr(action, "execute"):
            for item in action:
                await self._execute_action(item)
            return

        await action.execute(self.context)

    def register_handler(
        self, state: AmidakujiState, handler: HandlerSpec
    ) -> None:
        """外部からハンドラを上書き登録するためのヘルパー（主にテスト用）。"""

        self._registry.register(state, handler)
