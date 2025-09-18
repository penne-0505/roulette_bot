import pytest
from unittest.mock import MagicMock

import discord

from flow.actions import (
    DeferResponseAction,
    SendMessageAction,
    SendViewAction,
    ShowModalAction,
)
from models.context_model import CommandContext
from models.state_model import AmidakujiState


class DummyResponse:
    def __init__(self, *, done: bool = False):
        self._done = done
        self.sent_messages: list[dict] = []
        self.sent_modal = None
        self.deferred = None

    def is_done(self) -> bool:
        return self._done

    async def send_message(self, **payload):
        self.sent_messages.append(payload)

    async def send_modal(self, modal):
        self.sent_modal = modal

    async def defer(self, *, ephemeral: bool = True):
        self.deferred = ephemeral


class DummyFollowup:
    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send(self, **payload):
        self.sent_messages.append(payload)


@pytest.fixture
def context():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.response = DummyResponse(done=False)
    interaction.followup = DummyFollowup()
    interaction.user = MagicMock()

    context = CommandContext(
        interaction=interaction,
        state=AmidakujiState.COMMAND_EXECUTED,
    )
    context.result = interaction
    return context


@pytest.mark.asyncio
async def test_send_view_action_uses_initial_response(context):
    view = discord.ui.View()

    action = SendViewAction(view=view, ephemeral=False)
    await action.execute(context)

    assert context.interaction.response.sent_messages == [
        {"view": view, "ephemeral": False}
    ]
    assert context.interaction.followup.sent_messages == []


@pytest.mark.asyncio
async def test_send_view_action_forces_followup(context):
    view = discord.ui.View()

    action = SendViewAction(view=view, followup=True)
    await action.execute(context)

    assert context.interaction.followup.sent_messages == [
        {"view": view, "ephemeral": True}
    ]
    assert context.interaction.response.sent_messages == []


@pytest.mark.asyncio
async def test_send_message_action_includes_embeds_and_content(context):
    embed = discord.Embed(title="Hello")
    embeds = [discord.Embed(title="World")]

    action = SendMessageAction(
        content="greetings",
        embed=embed,
        embeds=embeds,
        ephemeral=False,
        followup=False,
    )
    await action.execute(context)

    assert context.interaction.response.sent_messages == [
        {
            "content": "greetings",
            "embed": embed,
            "embeds": embeds,
            "ephemeral": False,
        }
    ]


@pytest.mark.asyncio
async def test_send_message_action_defaults_to_followup_when_responded(context):
    context.interaction.response = DummyResponse(done=True)
    context.interaction.followup = DummyFollowup()

    action = SendMessageAction(content="done")
    await action.execute(context)

    assert context.interaction.followup.sent_messages == [
        {"content": "done", "ephemeral": True}
    ]


@pytest.mark.asyncio
async def test_show_modal_action_invokes_send_modal(context):
    modal = discord.ui.Modal(title="Modal")
    action = ShowModalAction(modal=modal)

    await action.execute(context)

    assert context.interaction.response.sent_modal is modal


@pytest.mark.asyncio
async def test_defer_response_action_skips_when_already_done(context):
    context.interaction.response = DummyResponse(done=True)
    action = DeferResponseAction(ephemeral=False)

    await action.execute(context)

    assert context.interaction.response.deferred is None


@pytest.mark.asyncio
async def test_defer_response_action_defers_when_pending(context):
    action = DeferResponseAction(ephemeral=False)

    await action.execute(context)

    assert context.interaction.response.deferred is False
