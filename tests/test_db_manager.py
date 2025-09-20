import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import utils
from db_manager import DBManager
from models.model import Template, TemplateScope, UserInfo
from models.model import Pair, PairList, SelectionMode, Template, TemplateScope, UserInfo

def test_get_embed_mode_initializes_missing_document():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_info_repository = MagicMock()
    mock_info_repository.read_document.return_value = None

    manager.info_repository = mock_info_repository
    manager.user_repository = object()
    manager.history_repository = MagicMock()
    manager.db = object()

    try:
        mode = manager.get_embed_mode()
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    assert mode == "compact"
    mock_info_repository.create_document.assert_called_once_with(
        "embed_mode", {"embed_mode": "compact"}
    )


def test_get_default_templates_initializes_when_missing_document():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_info_repository = MagicMock()
    # First call returns None to simulate missing document, second call returns initialized data
    mock_info_repository.read_document.side_effect = [None, {"default_templates": []}]

    manager.info_repository = mock_info_repository
    manager.user_repository = object()
    manager.history_repository = MagicMock()
    manager.db = object()

    try:
        templates = manager.get_default_templates()
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    assert templates == []
    mock_info_repository.create_document.assert_called_once()


def _make_doc(data: dict, *, doc_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=doc_id, to_dict=lambda: data)


def test_get_user_includes_shared_and_public_templates():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_user_repository = MagicMock()
    mock_user_repository.read_document.return_value = {
        "id": 1,
        "name": "Tester",
        "least_template": None,
        "custom_templates": [
            {"title": "My Template", "choices": ["A"], "scope": "private"}
        ],
    }

    mock_info_repository = MagicMock()
    mock_info_repository.read_document.return_value = {
        "default_templates": [
            {"title": "Default", "choices": ["D"], "scope": "public"}
        ]
    }

    guild_doc = _make_doc(
        {"title": "Guild Shared", "choices": ["G"], "scope": "guild"},
        doc_id="guild1",
    )
    public_doc = _make_doc(
        {"title": "Public Shared", "choices": ["P"], "scope": "public"},
        doc_id="public1",
    )

    def list_templates(*, scope=None, guild_id=None):
        if scope == TemplateScope.GUILD.value:
            return [guild_doc] if guild_id == 999 else []
        if scope == TemplateScope.PUBLIC.value:
            return [public_doc]
        return []

    mock_shared_repository = MagicMock()
    mock_shared_repository.list_templates.side_effect = list_templates

    manager.user_repository = mock_user_repository
    manager.info_repository = mock_info_repository
    manager.shared_template_repository = mock_shared_repository
    manager.db = object()

    try:
        user = manager.get_user(1, guild_id=999)
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    assert user is not None
    assert len(user.custom_templates) == 1
    assert len(user.shared_templates) == 1
    assert user.shared_templates[0].title == "Guild Shared"
    assert len(user.public_templates) == 2
    titles = {template.title for template in user.public_templates}
    assert titles == {"Public Shared", "Default"}


def test_copy_shared_template_to_user_generates_unique_title():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    existing_template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.PRIVATE,
    )
    user = UserInfo(id=1, name="Tester", custom_templates=[existing_template])

    manager.get_user = MagicMock(return_value=user)
    manager.add_custom_template = MagicMock()

    shared_template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.GUILD,
    )

    try:
        copied = manager.copy_shared_template_to_user(1, shared_template)
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    manager.add_custom_template.assert_called_once()
    args, _ = manager.add_custom_template.call_args
    assert args[0] == 1
    copied_template = args[1]
    assert copied_template.title == "Guild Shared (2)"
    assert copied.title == "Guild Shared (2)"

def test_get_selection_mode_initializes_missing_document():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_info_repository = MagicMock()
    mock_info_repository.read_document.return_value = None

    manager.info_repository = mock_info_repository
    manager.user_repository = object()
    manager.history_repository = MagicMock()
    manager.db = object()

    try:
        mode = manager.get_selection_mode()
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    assert mode == SelectionMode.RANDOM.value
    mock_info_repository.create_document.assert_called_once_with(
        "selection_mode", {"selection_mode": SelectionMode.RANDOM.value}
    )


def test_save_history_uses_history_repository():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_history_repository = MagicMock()
    manager.history_repository = mock_history_repository
    manager.info_repository = MagicMock()
    manager.user_repository = object()
    manager.db = object()

    template = Template(title="League", choices=["Top"])
    user = SimpleNamespace(id=1, display_name="Tester", name="Tester")
    pairs = PairList(pairs=[Pair(user=user, choice="Top")])

    try:
        manager.save_history(
            guild_id=42,
            template=template,
            pairs=pairs,
            selection_mode=SelectionMode.RANDOM,
        )
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    mock_history_repository.add_entry.assert_called_once()
    saved_data = mock_history_repository.add_entry.call_args.kwargs.get("data")
    if saved_data is None:
        saved_data = mock_history_repository.add_entry.call_args.args[0]
    assert saved_data["guild_id"] == 42
    assert saved_data["template_title"] == template.title
    assert saved_data["selection_mode"] == SelectionMode.RANDOM.value
    assert saved_data["entries"][0]["user_id"] == 1


def test_get_recent_history_converts_documents():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    mock_history_repository = MagicMock()
    mock_history_repository.fetch_recent.return_value = [
        {
            "guild_id": 1,
            "template_title": "League",
            "created_at": timestamp,
            "entries": [
                {"user_id": 1, "user_name": "Tester", "choice": "Top"}
            ],
            "choices": ["Top"],
            "selection_mode": SelectionMode.RANDOM.value,
        }
    ]

    manager.history_repository = mock_history_repository
    manager.info_repository = MagicMock()
    manager.user_repository = object()
    manager.db = object()

    try:
        histories = manager.get_recent_history(guild_id=1)
    finally:
        utils.Singleton._instances.pop(DBManager, None)

    assert len(histories) == 1
    history = histories[0]
    assert history.template_title == "League"
    assert history.entries[0].choice == "Top"
    assert history.created_at == timestamp
