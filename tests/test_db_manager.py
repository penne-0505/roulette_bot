from types import SimpleNamespace
from unittest.mock import MagicMock

import utils
from db_manager import DBManager
from models.model import Template, TemplateScope, UserInfo


def test_get_embed_mode_initializes_missing_document():
    utils.Singleton._instances.pop(DBManager, None)
    manager = DBManager.get_instance()

    mock_info_repository = MagicMock()
    mock_info_repository.read_document.return_value = None

    manager.info_repository = mock_info_repository
    manager.user_repository = object()
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
