import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from db_manager import (
    COLLECTION_SENTINEL_DOCUMENT_ID,
    DBManager,
    SharedTemplateRepository,
    REQUIRED_COLLECTIONS,
)
from models.model import (
    Pair,
    PairList,
    ResultEmbedMode,
    SelectionMode,
    Template,
    TemplateScope,
    UserInfo,
)


def reset_manager() -> None:
    DBManager.set_global_instance(None)

def test_get_embed_mode_initializes_missing_document():
    reset_manager()
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
        reset_manager()

    assert mode == "compact"
    mock_info_repository.create_document.assert_called_once_with(
        "embed_mode", {"embed_mode": "compact"}
    )


def test_set_embed_mode_updates_document():
    reset_manager()
    manager = DBManager.get_instance()

    mock_info_repository = MagicMock()
    mock_info_repository.read_document.return_value = {"embed_mode": "compact"}

    manager.info_repository = mock_info_repository
    manager.user_repository = object()
    manager.history_repository = MagicMock()
    manager.db = object()

    try:
        manager.set_embed_mode(ResultEmbedMode.DETAILED)
    finally:
        reset_manager()

    mock_info_repository.create_document.assert_called_once_with(
        "embed_mode", {"embed_mode": "detailed"}
    )


def test_get_default_templates_initializes_when_missing_document():
    reset_manager()
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
        reset_manager()

    assert templates == []
    mock_info_repository.create_document.assert_called_once()


def _make_doc(data: dict, *, doc_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=doc_id, to_dict=lambda: data)


def _make_document_ref(*, exists: bool) -> MagicMock:
    document_ref = MagicMock()
    document_ref.get.return_value = SimpleNamespace(exists=exists)
    return document_ref


def test_ensure_required_collections_creates_sentinel_documents():
    reset_manager()
    manager = DBManager.get_instance()

    collection_refs: dict[str, MagicMock] = {}
    document_refs: dict[str, MagicMock] = {}

    def collection_side_effect(name: str) -> MagicMock:
        collection_ref = MagicMock()
        document_ref = _make_document_ref(exists=False)
        collection_ref.document.return_value = document_ref
        collection_refs[name] = collection_ref
        document_refs[name] = document_ref
        return collection_ref

    db_mock = MagicMock()
    db_mock.collection.side_effect = collection_side_effect

    manager.db = db_mock
    manager.info_repository = MagicMock()
    manager.user_repository = MagicMock()
    manager.history_repository = MagicMock()

    try:
        manager.ensure_required_collections()
    finally:
        reset_manager()

    assert set(collection_refs) == set(REQUIRED_COLLECTIONS)
    for document_ref in document_refs.values():
        document_ref.set.assert_called_once()


def test_ensure_required_collections_skips_existing_sentinel():
    reset_manager()
    manager = DBManager.get_instance()

    document_refs: dict[str, MagicMock] = {}

    def collection_side_effect(name: str) -> MagicMock:
        collection_ref = MagicMock()
        document_ref = _make_document_ref(exists=True)
        collection_ref.document.return_value = document_ref
        document_refs[name] = document_ref
        return collection_ref

    db_mock = MagicMock()
    db_mock.collection.side_effect = collection_side_effect

    manager.db = db_mock
    manager.info_repository = MagicMock()
    manager.user_repository = MagicMock()
    manager.history_repository = MagicMock()

    try:
        manager.ensure_required_collections()
    finally:
        reset_manager()

    assert set(document_refs) == set(REQUIRED_COLLECTIONS)
    for document_ref in document_refs.values():
        document_ref.set.assert_not_called()


def test_shared_template_repository_list_skips_sentinel():
    db_mock = MagicMock()
    repo = SharedTemplateRepository(db_mock)

    sentinel_doc = SimpleNamespace(
        id=COLLECTION_SENTINEL_DOCUMENT_ID,
        to_dict=lambda: {},
    )
    real_doc = SimpleNamespace(
        id="real_doc",
        to_dict=lambda: {"scope": "public"},
    )

    repo.ref = MagicMock()
    repo.ref.stream.return_value = iter([sentinel_doc, real_doc])

    documents = repo.list_templates()

    assert documents == [real_doc]
    repo.ref.stream.assert_called_once()


def test_get_user_includes_shared_and_public_templates():
    reset_manager()
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
    manager.history_repository = MagicMock()
    manager.db = object()

    try:
        user = manager.get_user(1, guild_id=999)
    finally:
        reset_manager()

    assert user is not None
    assert len(user.custom_templates) == 1
    assert len(user.shared_templates) == 1
    assert user.shared_templates[0].title == "Guild Shared"
    assert len(user.public_templates) == 2
    titles = {template.title for template in user.public_templates}
    assert titles == {"Public Shared", "Default"}


def test_copy_shared_template_to_user_generates_unique_title():
    reset_manager()
    manager = DBManager.get_instance()

    existing_template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.PRIVATE,
    )
    user = UserInfo(id=1, name="Tester", custom_templates=[existing_template])

    manager.get_user = MagicMock(return_value=user)
    manager.add_custom_template = MagicMock()
    manager.history_repository = MagicMock()

    shared_template = Template(
        title="Guild Shared",
        choices=["A"],
        scope=TemplateScope.GUILD,
    )

    try:
        copied = manager.copy_shared_template_to_user(1, shared_template)
    finally:
        reset_manager()

    manager.add_custom_template.assert_called_once()
    args, _ = manager.add_custom_template.call_args
    assert args[0] == 1
    copied_template = args[1]
    assert copied_template.title == "Guild Shared (2)"
    assert copied.title == "Guild Shared (2)"

def test_get_selection_mode_initializes_missing_document():
    reset_manager()
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
        reset_manager()

    assert mode == SelectionMode.RANDOM.value
    mock_info_repository.create_document.assert_called_once_with(
        "selection_mode", {"selection_mode": SelectionMode.RANDOM.value}
    )


def test_save_history_uses_history_repository():
    reset_manager()
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
        reset_manager()

    mock_history_repository.add_entry.assert_called_once()
    saved_data = mock_history_repository.add_entry.call_args.kwargs.get("data")
    if saved_data is None:
        saved_data = mock_history_repository.add_entry.call_args.args[0]
    assert saved_data["guild_id"] == 42
    assert saved_data["template_title"] == template.title
    assert saved_data["selection_mode"] == SelectionMode.RANDOM.value
    assert saved_data["entries"][0]["user_id"] == 1


def test_get_recent_history_converts_documents():
    reset_manager()
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
        reset_manager()

    assert len(histories) == 1
    history = histories[0]
    assert history.template_title == "League"
    assert history.entries[0].choice == "Top"
    assert history.created_at == timestamp
