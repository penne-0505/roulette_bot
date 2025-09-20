import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import discord
import pytest

import data_process
from flow.actions import DeferResponseAction, EditMessageAction, SendMessageAction, SendViewAction
from flow.handlers import (
    OptionDeletedHandler,
    OptionMovedDownHandler,
    OptionMovedUpHandler,
    OptionNameEnteredHandler,
    OptionSelectionChangedHandler,
    DeleteTemplateModeHandler,
    MemberSelectedHandler,
    SharedTemplateCopyHandler,
    SharedTemplateSelectedHandler,
    TemplateCreatedHandler,
    TemplateDeletedHandler,
    TemplateDeterminedHandler,
    UseExistingHandler,
    UseHistoryHandler,
    UsePublicTemplatesHandler,
    UseSharedTemplatesHandler,
)
from models.context_model import CommandContext
from models.state_model import AmidakujiState
from views.view import (
    DeleteTemplateView,
    MemberSelectView,
    PublicTemplateSelectView,
    SelectTemplateView,
    SharedTemplateActionView,
    SharedTemplateSelectView,
    ApplyOptionsView,
)
from models.model import (
    AssignmentEntry,
    AssignmentHistory,
    Pair,
    PairList,
    SelectionMode,
    Template,
    UserInfo,
    TemplateScope
)

@pytest.fixture
def base_interaction():
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock(id=42)
    interaction.response = MagicMock()
    interaction.response.is_done.return_value = False
    interaction.followup = MagicMock()
    interaction.guild = None
    interaction.guild_id = 999
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
    assert len(action.view.children) == 2


@pytest.mark.asyncio
async def test_use_shared_templates_handler_requires_guild(base_interaction):
    base_interaction.guild_id = None
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_USE_SHARED,
    )
    context.result = base_interaction

    services = SimpleNamespace(db=MagicMock())
    handler = UseSharedTemplatesHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendMessageAction)
    assert action.embed is not None
    assert "サーバー内でのみ共有テンプレートを利用できます" in action.embed.description


@pytest.mark.asyncio
async def test_use_shared_templates_handler_returns_select_view(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_USE_SHARED,
    )
    context.result = base_interaction

    template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.GUILD,
    )
    user = UserInfo(id=42, name="Tester", shared_templates=[template])

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = UseSharedTemplatesHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, SharedTemplateSelectView)


@pytest.mark.asyncio
async def test_use_public_templates_handler_returns_select_view(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_USE_PUBLIC,
    )
    context.result = base_interaction

    template = Template(
        title="Public",
        choices=["A"],
        scope=TemplateScope.PUBLIC,
    )
    user = UserInfo(id=42, name="Tester", public_templates=[template])

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = UsePublicTemplatesHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, PublicTemplateSelectView)

async def test_option_name_entered_handler_updates_snapshot(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.OPTION_NAME_ENTERED,
    )
    context.result = ["Alpha", "Beta"]

    handler = OptionNameEnteredHandler()
    action = await handler.handle(context, SimpleNamespace())

    assert isinstance(action, SendMessageAction)
    assert action.embed is not None
    assert "2. **Beta**" in action.embed.description
    assert isinstance(action.view, ApplyOptionsView)
    assert context.options_snapshot == ["Alpha", "Beta"]
    assert context.option_edit_index == 1


@pytest.mark.asyncio
async def test_option_selection_changed_handler_updates_index(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.OPTION_MANAGE_SELECTED,
    )
    context.result = 1
    context.set_option_snapshot(["Alpha", "Beta"], preferred_index=0)

    handler = OptionSelectionChangedHandler()
    action = await handler.handle(context, SimpleNamespace())

    assert isinstance(action, EditMessageAction)
    assert isinstance(action.view, ApplyOptionsView)
    assert context.option_edit_index == 1
    assert action.embed is not None
    assert "2. **Beta**" in action.embed.description


@pytest.mark.asyncio
async def test_option_deleted_handler_removes_option(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.OPTION_DELETED,
    )
    context.result = base_interaction
    context.set_option_snapshot(["Alpha", "Beta", "Gamma"], preferred_index=1)

    handler = OptionDeletedHandler()
    actions = await handler.handle(context, SimpleNamespace())

    assert isinstance(actions, list)
    assert isinstance(actions[0], EditMessageAction)
    assert isinstance(actions[1], SendMessageAction)
    assert "Beta" in (actions[1].content or "")
    assert context.options_snapshot == ["Alpha", "Gamma"]
    assert context.option_edit_index == 1


@pytest.mark.asyncio
async def test_option_moved_up_handler_swaps_options(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.OPTION_MOVED_UP,
    )
    context.result = base_interaction
    context.set_option_snapshot(["Alpha", "Beta", "Gamma"], preferred_index=1)

    handler = OptionMovedUpHandler()
    actions = await handler.handle(context, SimpleNamespace())

    assert isinstance(actions, list)
    assert isinstance(actions[0], EditMessageAction)
    assert context.options_snapshot == ["Beta", "Alpha", "Gamma"]
    assert context.option_edit_index == 0
    assert isinstance(actions[1], SendMessageAction)
    assert "Beta" in (actions[1].content or "")


@pytest.mark.asyncio
async def test_option_moved_down_handler_swaps_options(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.OPTION_MOVED_DOWN,
    )
    context.result = base_interaction
    context.set_option_snapshot(["Alpha", "Beta", "Gamma"], preferred_index=1)

    handler = OptionMovedDownHandler()
    actions = await handler.handle(context, SimpleNamespace())

    assert isinstance(actions, list)
    assert isinstance(actions[0], EditMessageAction)
    assert context.options_snapshot == ["Alpha", "Gamma", "Beta"]
    assert context.option_edit_index == 2
    assert isinstance(actions[1], SendMessageAction)
    assert "Beta" in (actions[1].content or ""


@pytest.mark.asyncio
async def test_template_created_handler_updates_context_and_saves_template(base_interaction):
    template = Template(title="Valorant", choices=["Duelist", "Initiator"])
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
async def test_template_created_handler_rejects_single_option(base_interaction):
    template = Template(title="Solo", choices=["Only"])
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.TEMPLATE_CREATED,
    )
    context.result = template

    services = SimpleNamespace(db=MagicMock())

    handler = TemplateCreatedHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendMessageAction)
    assert action.embed is not None
    assert "2件以上" in action.embed.description
    services.db.add_custom_template.assert_not_called()


@pytest.mark.asyncio
async def test_delete_template_mode_handler_returns_delete_view(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_DELETE_TEMPLATE,
    )
    context.result = base_interaction

    template = Template(title="League", choices=["Top"])
    user = UserInfo(id=42, name="Tester", custom_templates=[template])

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = DeleteTemplateModeHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, DeleteTemplateView)


@pytest.mark.asyncio
async def test_delete_template_mode_handler_returns_error_when_no_templates(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MODE_DELETE_TEMPLATE,
    )
    context.result = base_interaction

    user = UserInfo(id=42, name="Tester", custom_templates=[])

    services = SimpleNamespace(db=MagicMock())
    services.db.get_user.return_value = user

    handler = DeleteTemplateModeHandler()
    action = await handler.handle(context, services)

    assert isinstance(action, SendMessageAction)
    assert action.embed is not None
    assert "削除できるテンプレート" in action.embed.description


@pytest.mark.asyncio
async def test_template_deleted_handler_deletes_template(base_interaction):
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.TEMPLATE_DELETED,
    )
    context.result = "League"

    services = SimpleNamespace(db=MagicMock())

    handler = TemplateDeletedHandler()
    actions = await handler.handle(context, services)

    services.db.delete_custom_template.assert_called_once_with(
        user_id=42, template_title="League"
    )
    assert isinstance(actions, list)
    assert isinstance(actions[0], DeferResponseAction)
    assert isinstance(actions[1], SendMessageAction)
    assert context.state is AmidakujiState.MODE_USE_EXISTING
    assert context.result is base_interaction


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
async def test_shared_template_selected_handler_returns_action_view(base_interaction):
    template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.GUILD,
    )
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.SHARED_TEMPLATE_SELECTED,
    )
    context.result = template

    handler = SharedTemplateSelectedHandler()
    action = await handler.handle(context, services=None)

    assert isinstance(action, SendViewAction)
    assert isinstance(action.view, SharedTemplateActionView)
    assert action.followup is True


@pytest.mark.asyncio
async def test_shared_template_copy_handler_invokes_copy(base_interaction):
    template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.GUILD,
    )
    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.SHARED_TEMPLATE_COPY_REQUESTED,
    )
    context.result = template

    copied = Template(title="Guild Shared (2)", choices=["A"])
    services = SimpleNamespace(db=MagicMock())
    services.db.copy_shared_template_to_user.return_value = copied

    handler = SharedTemplateCopyHandler()
    action = await handler.handle(context, services)

    services.db.copy_shared_template_to_user.assert_called_once_with(42, template)
    assert isinstance(action, SendMessageAction)
    assert action.followup is True


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

    def fake_create_pair_from_list(users, choices, *, selection_mode, weights):
        assert users == selected_members
        assert choices == template.choices
        assert selection_mode is SelectionMode.RANDOM
        assert weights is None
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
    services.db.get_selection_mode.return_value = SelectionMode.RANDOM.value
    services.db.get_recent_history.return_value = []

    handler = MemberSelectedHandler()
    action = await handler.handle(context, services)

    services.db.get_embed_mode.assert_called_once()
    services.db.get_selection_mode.assert_called_once()
    services.db.get_recent_history.assert_called_once()
    services.db.save_history.assert_called_once()
    assert isinstance(action, SendMessageAction)
    assert action.embeds is embeds
    assert action.ephemeral is False


@pytest.mark.asyncio
async def test_member_selected_handler_detects_bias(monkeypatch, base_interaction):
    user = MagicMock(spec=discord.User)
    user.id = 123
    user.display_name = "Tester"

    selected_members = [user]
    template = Template(title="League", choices=["Top"])

    context = CommandContext(
        interaction=base_interaction,
        state=AmidakujiState.MEMBER_SELECTED,
    )
    context.result = selected_members
    context.history[AmidakujiState.TEMPLATE_DETERMINED] = template

    pair_list = PairList(pairs=[Pair(user=user, choice="Top")])

    def fake_create_pair_from_list(*args, **kwargs):
        assert kwargs["selection_mode"] is SelectionMode.BIAS_REDUCTION
        weights = kwargs["weights"]
        assert weights is not None
        assert weights[user.id]["Top"] < 1.0
        return pair_list

    embeds = [discord.Embed(title="Result")]

    def fake_create_embeds_from_pairs(*, pairs, mode):
        assert pairs is pair_list
        return embeds

    monkeypatch.setattr(data_process, "create_pair_from_list", fake_create_pair_from_list)
    monkeypatch.setattr(data_process, "create_embeds_from_pairs", fake_create_embeds_from_pairs)

    base_time = datetime.datetime.now(datetime.timezone.utc)
    histories = [
        AssignmentHistory(
            guild_id=base_interaction.guild_id or 0,
            template_title=template.title,
            created_at=base_time - datetime.timedelta(minutes=idx + 1),
            entries=[AssignmentEntry(user_id=user.id, user_name="Tester", choice="Top")],
            selection_mode=SelectionMode.RANDOM,
        )
        for idx in range(3)
    ]

    services = SimpleNamespace(db=MagicMock())
    services.db.get_embed_mode.return_value = "compact"
    services.db.get_selection_mode.return_value = SelectionMode.BIAS_REDUCTION.value
    services.db.get_recent_history.return_value = histories

    handler = MemberSelectedHandler()
    actions = await handler.handle(context, services)

    assert isinstance(actions, list)
    assert len(actions) == 2
    assert isinstance(actions[0], SendMessageAction)
    warning_action = actions[1]
    assert isinstance(warning_action, SendMessageAction)
    assert warning_action.ephemeral is True
    assert warning_action.embed is not None
    assert "偏り" in warning_action.embed.title
