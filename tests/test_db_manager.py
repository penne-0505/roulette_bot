from unittest.mock import MagicMock

import utils
from db_manager import DBManager


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
