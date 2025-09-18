import pytest
from unittest.mock import MagicMock

import discord

from models.context_model import CommandContext
from models.state_model import AmidakujiState


@pytest.fixture
def mock_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    return interaction


def test_command_context_updates_history_and_result(mock_interaction):
    context = CommandContext(interaction=mock_interaction, state=AmidakujiState.COMMAND_EXECUTED)

    context.result = mock_interaction

    assert context.result is mock_interaction
    assert context.history[AmidakujiState.COMMAND_EXECUTED] is mock_interaction


def test_command_context_rejects_invalid_result_type(mock_interaction):
    context = CommandContext(interaction=mock_interaction, state=AmidakujiState.TEMPLATE_TITLE_ENTERED)

    with pytest.raises(TypeError):
        context.result = 42


def test_update_context_replaces_interaction(mock_interaction):
    context = CommandContext(interaction=mock_interaction, state=AmidakujiState.COMMAND_EXECUTED)
    context.result = mock_interaction

    new_interaction = MagicMock(spec=discord.Interaction)
    new_interaction.user = MagicMock()

    context.update_context(
        state=AmidakujiState.MODE_CREATE_NEW,
        result=new_interaction,
        interaction=new_interaction,
    )

    assert context.interaction is new_interaction
    assert context.state is AmidakujiState.MODE_CREATE_NEW
    assert context.result is new_interaction
    assert context.history[AmidakujiState.MODE_CREATE_NEW] is new_interaction
