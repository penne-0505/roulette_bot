import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord

from domain import UserInfo
from data_interface import FlowController
from flow.actions import FlowAction
from flow.handlers import BaseStateHandler
from models.context_model import CommandContext
from models.state_model import AmidakujiState


class DummyAction:
    def __init__(self):
        self.executed = False

    async def execute(self, context: CommandContext) -> None:
        self.executed = True
        context.update_context(
            state=AmidakujiState.CANCELLED,
            result=context.interaction,
            interaction=context.interaction,
        )


class DummyHandler(BaseStateHandler):
    def __init__(self, action: FlowAction):
        self._action = action
        self.called_with: tuple[CommandContext, object] | None = None

    async def handle(self, context: CommandContext, services):
        self.called_with = (context, services)
        return self._action


@pytest.fixture
def controller():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done.return_value = False
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    context = CommandContext(
        interaction=interaction,
        state=AmidakujiState.COMMAND_EXECUTED,
    )
    context.result = interaction

    services = SimpleNamespace()
    controller = FlowController(context=context, services=services)
    return controller, context, services


@pytest.mark.asyncio
async def test_dispatch_runs_handler_and_updates_context(controller):
    controller, context, services = controller
    action = DummyAction()
    handler = DummyHandler(action)

    controller._handlers[AmidakujiState.MODE_CREATE_NEW] = handler

    await controller.dispatch(
        AmidakujiState.MODE_CREATE_NEW,
        context.interaction,
        context.interaction,
    )

    assert action.executed is True
    assert handler.called_with == (context, services)
    assert context.state is AmidakujiState.CANCELLED
    assert context.services is services


@pytest.mark.asyncio
async def test_execute_action_handles_sequence(controller):
    controller, context, _ = controller

    action1 = SimpleNamespace(execute=AsyncMock())
    action2 = SimpleNamespace(execute=AsyncMock())

    await controller._execute_action([action1, action2])

    action1.execute.assert_awaited_once_with(context)
    action2.execute.assert_awaited_once_with(context)


@pytest.mark.asyncio
async def test_dispatch_raises_for_unknown_state(controller):
    controller, context, _ = controller

    with pytest.raises(ValueError):
        await controller.dispatch(
            AmidakujiState.COMMAND_EXECUTED,
            context.interaction,
            context.interaction,
        )


@pytest.mark.asyncio
async def test_dispatch_template_deleted_transitions_to_use_existing():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock(id=42)
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done.return_value = True
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    context = CommandContext(
        interaction=interaction,
        state=AmidakujiState.MODE_DELETE_TEMPLATE,
    )
    context.result = interaction

    services = SimpleNamespace(
        db=MagicMock(
            delete_custom_template=MagicMock(),
            get_user=MagicMock(return_value=UserInfo(id=42, name="Tester")),
        )
    )

    controller = FlowController(context=context, services=services)

    await controller.dispatch(
        AmidakujiState.TEMPLATE_DELETED,
        "Obsolete Template",
        interaction,
    )

    services.db.delete_custom_template.assert_called_once_with(
        user_id=42,
        template_title="Obsolete Template",
    )
    assert context.state is AmidakujiState.MODE_USE_EXISTING
    followup_calls = interaction.followup.send.call_args_list
    assert followup_calls, "フォローアップメッセージが送信されていること"
    assert any("embed" in kwargs or "embeds" in kwargs for _, kwargs in followup_calls)
