import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

import discord

import data_process
from flow.actions import DeferResponseAction, SendMessageAction, SendViewAction
from flow.handlers import (
    MemberSelectedHandler,
    TemplateCreatedHandler,
    TemplateDeterminedHandler,
    UseExistingHandler,
    UseHistoryHandler,
)
from models.context_model import CommandContext
from models.model import Template, UserInfo
from models.state_model import AmidakujiState
from views.view import MemberSelectView, SelectTemplateView


@pytest.fixture
def base_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock(id=42)
    interaction.response = MagicMock()
    interaction.followup = MagicMock()
    return interaction


@pytest.mark.asyncio
async def test_use_existing_handler_returns_select_view(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_USE_EXISTING,
    )
    context.result = base_interaction

    template = Template(title="League", choices=["Top"])
    user = UserInfo(id=42, name="Tester", custom_templates=[template])

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = UseExistingHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, SelectTemplateView)
    assert len(action.view.children) == 1


@pytest.mark.asyncio
async def test_template_created_handler_updates_context_and_saves_template(base_interaction):
    template = Template(title="Valorant", choices=["Duelist"])
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.TEMPLATE_CREATED,
    )
    context.result = template

    services = SimpleNamespace(db=MagicMock())

    handler = TemplateCreatedHandler()
    actions = await handler.handle(context, services)

    assert isinstance(actions, list)
    assert isinstance(actions[0], DeferResponseAction)
    assert isinstance(actions[1], SendMessageAction)
    services.db.add_custom_template.assert_called_once_with(
        user_id=42, template=template
    )
    assert context.state is AmidakujiState.TEMPLATE_DETERMINED
    assert context.result is template


@pytest.mark.asyncio
async def test_use_history_handler_returns_error_when_missing_history(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_USE_HISTORY,
    )
    context.result = base_interaction

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = UserInfo(id=42, name="Tester")

    handler = UseHistoryHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendMessageAction)
    assert "履歴が見つかりませんでした" in action.embed.description
    assert context.state is AmidakujiState.MODE_USE_HISTORY


@pytest.mark.asyncio
async def test_use_history_handler_returns_followup_when_history_exists(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.COMMAND_EXECUTED,
    )
    context.result = base_interaction
    context.update_context(
        state=AmidakujiState.MODE_USE_HISTORY,
        result=base_interaction,
        interaction=base_interaction,
    )

    template = Template(title="Saved", choices=["A", "B"])
    user = UserInfo(id=42, name="Tester", least_template=template)

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = UseHistoryHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendMessageAction)
    assert action.followup is True
    assert action.interaction is context.history[AmidakujiState.COMMAND_EXECUTED]
    assert context.state is AmidakujiState.TEMPLATE_DETERMINED
    assert context.result is template


@pytest.mark.asyncio
async def test_template_determined_handler_returns_member_select_view(base_interaction):
    template = Template(title="League", choices=["Top"])
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.TEMPLATE_DETERMINED,
    )
    context.result = template

    services = SimpleNamespace(db=MagicMock())

    handler = TemplateDeterminedHandler()
    action = await handler.handle(context, services)

    services.db.set_least_template.assert_called_once_with(42, template)
    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, MemberSelectView)


@pytest.mark.asyncio
async def test_member_selected_handler_builds_embeds(monkeypatch, base_interaction):
    selected_members = [
        MagicMock(spec=discord.User),
        MagicMock(spec=discord.User),
    ]
    template = Template(title="League", choices=["Top", "Jungle"])

    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MEMBER_SELECTED,
    )
    context.result = selected_members
    context.history[AmidakujiState.TEMPLATE_DETERMINED] = template

    pair_list = MagicMock()

    def fake_create_pair_from_list(users, choices):
        assert users == selected_members
        assert choices == template.choices
        return pair_list

    embeds = [discord.Embed(title="Result")]

    def fake_create_embeds_from_pairs(*, pairs, mode):
        assert pairs is pair_list
        assert mode == "compact"
        return embeds

    monkeypatch.setattr(data_process, "create_pair_from_list", fake_create_pair_from_list)
    monkeypatch.setattr(data_process, "create_embeds_from_pairs", fake_create_embeds_from_pairs)

    services = SimpleNamespace(db=MagicMock())
    services.db.get_embed_mode.return_value = "compact"

    handler = MemberSelectedHandler()
    action = await handler.handle(context, services)

    services.db.get_embed_mode.assert_called_once()
    assert isinstance(action, SendMessageAction)
    assert action.embeds is embeds
    assert action.ephemeral is False
