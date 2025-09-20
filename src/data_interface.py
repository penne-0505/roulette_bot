"""Flow controller that dispatches Amidakuji states to handlers."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import discord

from flow.actions import FlowAction
from flow.handlers import (
    BaseStateHandler,
    CancelledHandler,
    CreateNewHandler,
    DeleteTemplateModeHandler,
    EnterOptionButtonHandler,
    MemberSelectedHandler,
    NeedMoreOptionsHandler,
    OptionDeletedHandler,
    OptionMovedDownHandler,
    OptionMovedUpHandler,
    OptionSelectionChangedHandler,
    OptionNameEnteredHandler,
    SharedTemplateCopyHandler,
    SharedTemplateSelectedHandler,
    TemplateDeletedHandler,
    TemplateCreatedHandler,
    TemplateDeterminedHandler,
    TemplateTitleEnteredHandler,
    UseExistingHandler,
    UsePublicTemplatesHandler,
    UseSharedTemplatesHandler,
    UseHistoryHandler,
)
from models.context_model import CommandContext
from models.state_model import AmidakujiState


class FlowController:
    """Dispatch handlers for the current state and execute resulting actions."""

    def __init__(self, context: CommandContext, services: Any) -> None:
        self.context = context
        self.services = services
        self._handlers: dict[AmidakujiState, BaseStateHandler] = {
            AmidakujiState.MODE_USE_EXISTING: UseExistingHandler(),
            AmidakujiState.MODE_CREATE_NEW: CreateNewHandler(),
            AmidakujiState.MODE_USE_HISTORY: UseHistoryHandler(),
            AmidakujiState.MODE_DELETE_TEMPLATE: DeleteTemplateModeHandler(),
            AmidakujiState.MODE_USE_SHARED: UseSharedTemplatesHandler(),
            AmidakujiState.MODE_USE_PUBLIC: UsePublicTemplatesHandler(),
            AmidakujiState.TEMPLATE_TITLE_ENTERED: TemplateTitleEnteredHandler(),
            AmidakujiState.ENTER_OPTION_BUTTON_CLICKED: EnterOptionButtonHandler(),
            AmidakujiState.OPTION_NAME_ENTERED: OptionNameEnteredHandler(),
            AmidakujiState.OPTION_MANAGE_SELECTED: OptionSelectionChangedHandler(),
            AmidakujiState.OPTION_DELETED: OptionDeletedHandler(),
            AmidakujiState.OPTION_MOVED_UP: OptionMovedUpHandler(),
            AmidakujiState.OPTION_MOVED_DOWN: OptionMovedDownHandler(),
            AmidakujiState.NEED_MORE_OPTIONS: NeedMoreOptionsHandler(),
            AmidakujiState.TEMPLATE_CREATED: TemplateCreatedHandler(),
            AmidakujiState.TEMPLATE_DELETED: TemplateDeletedHandler(),
            AmidakujiState.TEMPLATE_DETERMINED: TemplateDeterminedHandler(),
            AmidakujiState.MEMBER_SELECTED: MemberSelectedHandler(),
            AmidakujiState.SHARED_TEMPLATE_SELECTED: SharedTemplateSelectedHandler(),
            AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED: SharedTemplateCopyHandler(),
            AmidakujiState.CANCELLED: CancelledHandler(),
        }

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
            handler = self._handlers.get(current_state)
            if handler is None:
                raise ValueError(f"Invalid state: {current_state}")

            actions = await handler.handle(self.context, self.services)
            await self._execute_action(actions)

            if self.context.state == current_state:
                break

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
